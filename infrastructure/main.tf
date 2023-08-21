# Terraform and Provider Configuration
terraform {
  required_version = ">= 1.0"
  backend "s3" {
    bucket  = "tf-state-xgoals-mlops"
    key     = "mlops-xgoals-stg.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current_identity" {}

data "aws_vpc" "default" {
  default = true
}

data "http" "myip" {
  url = "http://ipv4.icanhazip.com"
}



module "sg_ssh" {
  source = "terraform-aws-modules/security-group/aws"

  name        = "sg_ssh-${var.project_id}"
  description = "Security group for ec2 ssh"
  vpc_id      = data.aws_vpc.default.id

  ingress_cidr_blocks = ["${chomp(data.http.myip.body)}/32"]
  ingress_rules       = ["ssh-tcp"]
}

module "sg_web" {
  source = "terraform-aws-modules/security-group/aws"

  name        = "sg_web-${var.project_id}"
  description = "Security group for ec2_web"
  vpc_id      = data.aws_vpc.default.id

  ingress_cidr_blocks = ["0.0.0.0/0"]
  ingress_rules       = ["http-80-tcp", "http-8080-tcp", "https-443-tcp", "all-icmp"]
  egress_rules        = ["all-all"]
}


module "mlflow_rds_sg" {
  source = "terraform-aws-modules/security-group/aws"

  name        = "mlflow_rds_sg-${var.project_id}"
  description = "Security group for db"
  vpc_id      = data.aws_vpc.default.id

  ingress_with_source_security_group_id = [
    {
      description              = "postgres db access"
      rule                     = "postgresql-tcp"
      source_security_group_id = module.sg_web.security_group_id
    }
  ]
  egress_rules = ["all-all"]
}

locals {
  account_id = data.aws_caller_identity.current_identity.account_id
  user_data_mlflow_server = trimspace(
    <<-EOF
      #!/bin/bash
      set -ex
      sudo yum update -y
      sudo amazon-linux-extras install docker -y
      sudo service docker start
      sudo usermod -a -G docker ec2-user
      sudo curl -L $(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r ".assets[] | select(.name | contains(\"linux-x86_64\")) | .browser_download_url") -o /usr/local/bin/docker-compose
      sudo chmod +x /usr/local/bin/docker-compose
      pip3 install mlflow boto3 psycopg2-binary
      mlflow server -h 0.0.0.0 -p 5000 --backend-store-uri postgresql://${var.mlflow_postgres_db_username}:${var.mlflow_postgres_db_password}@${module.mlflow_rds.endpoint}/${var.mlflow_postgres_db_name} --default-artifact-root s3://${var.model_bucket}/
    EOF
  )
  mlflow_tracking_uri = "http://${module.ec2_mlflow.external_ip}:5000"
}

# RDS Configuration
module "mlflow_rds" {
  source               = "./modules/rds_mlflow"
  mlflow_rds_identifier       = var.mlflow_rds_identifier
  mlflow_postgres_db_name     = var.mlflow_postgres_db_name
  mlflow_postgres_db_username = var.mlflow_postgres_db_username
  mlflow_postgres_db_password = var.mlflow_postgres_db_password
  mlflow_rds_sg_id = [module.mlflow_rds_sg.security_group_id]
}

module "monitoring_rds" {
  source               = "./modules/monitoring_rds"
  # monitoring_rds_identifier       = var.monitoring_rds_identifier
  monitoring_postgres_db_name     = var.monitoring_postgres_db_name
  monitoring_postgres_db_username = var.monitoring_postgres_db_username
  monitoring_postgres_db_password = var.monitoring_postgres_db_password
}

# EC2 Configuration
module "ec2_mlflow" {
  source                     = "./modules/ec2_mlflow"
  user_data                  = local.user_data_mlflow_server
  key_name                   = "ec2_key_name_mlflow-${var.project_id}"
  ssh_key_filename           = "ec2_ssh_key_mlflow-${var.project_id}.pem"
  security_groups = [
  module.sg_web.security_group_id,
  module.sg_ssh.security_group_id,
  aws_security_group.mlflow_server_sg.id,
  aws_security_group.adminer_sg.id,
  aws_security_group.grafana_sg.id
]



  tags                       = { Name = "ec2_server_mlflow-${var.project_id}", Project = var.project_id }
  ec2_iam_role_name          = "ec2_iam_role-${var.project_id}"
  ec2_instance_profile_name  = "ec2_instance_profile-${var.project_id}"
  s3_iam_role_policy_name    = "s3_iam_role_policy-${var.project_id}"
  s3_bucket_name             = var.model_bucket
  mlflow_postgres_endpoint = module.mlflow_rds.endpoint
  # mlflow_postgres_db_name           = var.mlflow_postgres_db_name
  # mlflow_postgres_db_username       = var.mlflow_postgres_db_username
  # mlflow_postgres_db_password       = var.mlflow_postgres_db_password
}

# Kinesis Streams
module "source_kinesis_stream" {
  source           = "./modules/kinesis"
  retention_period = 48
  shard_count      = 2
  stream_name      = "${var.source_stream_name}-${var.project_id}"
  tags             = var.project_id
}

module "output_kinesis_stream" {
  source           = "./modules/kinesis"
  retention_period = 48
  shard_count      = 2
  stream_name      = "${var.output_stream_name}-${var.project_id}"
  tags             = var.project_id
}

# S3 Bucket for Models
module "s3_bucket" {
  source      = "./modules/s3"
  bucket_name = "${var.model_bucket}-${var.project_id}"
}

# ECR and Lambda
module "ecr_image" {
  source                    = "./modules/ecr"
  ecr_repo_name             = "${var.ecr_repo_name}_${var.project_id}"
  account_id                = local.account_id
  lambda_function_local_path = var.lambda_function_local_path
  docker_image_local_path   = var.docker_image_local_path
}

module "lambda_function" {
  source              = "./modules/lambda"
  image_uri           = module.ecr_image.image_uri
  lambda_function_name = "${var.lambda_function_name}_${var.project_id}"
  model_bucket        = module.s3_bucket.name
  output_stream_name  = "${var.output_stream_name}-${var.project_id}"
  output_stream_arn   = module.output_kinesis_stream.stream_arn
  source_stream_name  = "${var.source_stream_name}-${var.project_id}"
  source_stream_arn   = module.source_kinesis_stream.stream_arn
}

# Outputs for CI/CD
output "lambda_function" {
  value = "${var.lambda_function_name}_${var.project_id}"
}

output "model_bucket" {
  value = module.s3_bucket.name
}

output "predictions_stream_name" {
  value = "${var.output_stream_name}-${var.project_id}"
}

output "ecr_repo" {
  value = "${var.ecr_repo_name}_${var.project_id}"
}

output "mlflow_tracking_uri" {
  value = local.mlflow_tracking_uri
}

output "mlflow_rds_endpoint" {
  value = module.mlflow_rds.endpoint
}


# Security Groups
resource "aws_security_group" "mlflow_server_sg" {
  name        = "mlflow_server_sg"
  description = "Allow inbound traffic for MLflow Server"
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "mlflow_rds_sg" {
  name        = "mlflow_rds_sg"
  description = "Allow inbound traffic for MLflow RDS"
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "adminer_sg" {
  name        = "adminer_security_group"
  description = "Allow inbound traffic on port 8081 for Adminer"
  ingress {
    from_port   = 8081
    to_port     = 8081
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "grafana_sg" {
  name        = "grafana_security_group"
  description = "Allow inbound traffic on port 3000 for Grafana"
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
