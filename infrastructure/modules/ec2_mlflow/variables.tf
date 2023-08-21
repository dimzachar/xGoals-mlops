variable "ssh_key_filename" {
  description = "Filename for storing ssh private key"
  default = "ec2_ssh_key.pem"
}

variable "key_name" {
  description = "Name of the ssh key pair"
  default = "ec2_ssh_key"
}

variable "instance_type" {
  description = "Instance type"
  default     = "t3.micro"
}

variable "security_groups" {
  description = "List of security groups of the instance"
  type        = list(string)
}

variable "tags" {
  description = "Dict of tags of the instance"
  default = {
    Name = "ec2_server"
    Project = "ec2_server_project"
  }
}

variable "ec2_iam_role_name" {
  description = "Name of the ec2 iam role"
  default     = "ec2_iam_role"
}

variable "ec2_instance_profile_name" {
  description = "Name of the ec2 instance profile"
  default     = "ec2_instance_profile"
}

variable "s3_iam_role_policy_name" {
  description = "Name of the s3 iam role policy"
  default     = "s3_iam_role_policy"
}

variable "s3_bucket_name" {
  description = "Name of the bucket"
}

variable "mlflow_postgres_endpoint" {
  description = "Endpoint of the rds instance"
}

variable "mlflow_postgres_db_name" {
  description = "Name of db in rds instance"
  default     = "db"
}

variable "mlflow_postgres_db_username" {
  description = "User name of rds db"
  default     = "db_user"
}

variable "mlflow_postgres_db_password" {
  description = "Password of rds db"
  default     = "db_password"
}

variable "user_data" {
  description = "Initialization script"
}