# mlflow_postgresQL RDS
resource "aws_db_instance" "mlflow_rds" {
  allocated_storage    = 20
  storage_type         = "gp2"
  engine               = "postgres"
  engine_version       = "14.7"
  instance_class       = "db.t3.micro"
  identifier           = var.mlflow_rds_identifier
  db_name              = var.mlflow_postgres_db_name
  username             = var.mlflow_postgres_db_username
  password             = var.mlflow_postgres_db_password
  skip_final_snapshot  = true
  vpc_security_group_ids = var.mlflow_rds_sg_id
}

output "endpoint" {
  value = aws_db_instance.mlflow_rds.endpoint
}