resource "aws_db_instance" "monitoring_rds" {
  allocated_storage    = var.allocated_storage
  storage_type         = "gp2"
  engine               = "postgres"
  engine_version       = "13"
  instance_class       = var.instance_class
  name                 = var.monitoring_postgres_db_name
  username             = var.monitoring_postgres_db_username
  password             = var.monitoring_postgres_db_password
  parameter_group_name = "default.postgres13"
  skip_final_snapshot  = true
  tags = {
    Name = "ModelMonitoringDB"
  }
}
