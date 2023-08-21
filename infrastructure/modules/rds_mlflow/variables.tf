# MLflow RDS Configuration
variable "mlflow_rds_identifier" {
  description = "The identifier for the MLflow RDS instance"
  default     = "mlflow-db"
   type        = string
}

variable "mlflow_postgres_db_name" {
  description = "The name of the default database for MLflow"
  default     = "mlflow_db"
   type        = string
}

variable "mlflow_postgres_db_username" {
  description = "Username for the MLflow RDS database"
  default     = "mlflow_user"
   type        = string
}

variable "mlflow_postgres_db_password" {
  description = "Password for the MLflow RDS database"
   type        = string
  default     = "mlflow_password"
  sensitive   = true
}

variable "mlflow_rds_sg_id" {
    description = "Security Group ID for MLflow RDS"
}