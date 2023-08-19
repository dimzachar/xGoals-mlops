# # EC2 instance for computation
# resource "aws_instance" "ml_instance" {
#   ami           = "ami-0c94855ba95c574c8" # Replace with the appropriate AMI
#   instance_type = "t2.micro"

#   tags = {
#     Name        = "ML Instance"
#     Environment = "MLOps"
#   }
# }

# PostgreSQL RDS
resource "aws_db_instance" "mlflow_rds" {
  allocated_storage    = 20
  storage_type         = "gp2"
  engine               = "postgres"
  engine_version       = "14.7"
  instance_class       = "db.t3.micro"
  identifier           = var.rds_identifier
  db_name              = var.postgres_db_name
  username             = var.postgres_db_username
  password             = var.postgres_db_password
  skip_final_snapshot  = true
  vpc_security_group_ids = [aws_security_group.mlflow_rds_sg.id]
}
resource "aws_security_group" "mlflow_rds_sg" {
  name        = "mlflow_rds_sg"
  description = "Allow inbound traffic for MLflow RDS"

  # Inbound rule to allow all traffic from security group sg-0904e49e8ef99e90e
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    security_groups = ["sg-0904e49e8ef99e90e"]
}


  # Inbound rule to allow PostgreSQL traffic from security group sg-0eaa83fac877bf113
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = ["sg-0eaa83fac877bf113"]
  }

  # Allow all outbound traffic (default behavior)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
