variable "aws_region" {
  description = "AWS region to create resources"
  default     = "us-east-1"
}

variable "project_id" {
  description = "project_id"
  default = "mlops-xgoals"
}
# For MLflow RDS
variable "mlflow_rds_identifier" {
  description = "The identifier for the MLflow RDS instance"
  type        = string
  default     = "mlflow-db"
}

variable "mlflow_postgres_db_name" {
  description = "The name of the default database for MLflow"
  type        = string
  default     = "mlflow_db"
}

variable "mlflow_postgres_db_username" {
  description = "Username for the MLflow RDS database"
  type        = string
  default     = "mlflow_user"
}

variable "mlflow_postgres_db_password" {
  description = "Password for the MLflow RDS database"
  type        = string
  default     = "mlflow_password"
  sensitive   = true
}

# For Model Monitoring RDS
variable "monitoring_rds_identifier" {
  description = "The identifier for the model monitoring RDS instance"
  type        = string
  default     = "model-monitoring-db"
}

variable "monitoring_postgres_db_name" {
  description = "The name of the default database for model monitoring"
  type        = string
  default     = "model_monitoring"
}

variable "monitoring_postgres_db_username" {
  description = "Username for the model monitoring RDS database"
  type        = string
  default     = "monitoring_user"
}

variable "monitoring_postgres_db_password" {
  description = "Password for the model monitoring RDS database"
  type        = string
  default     = "monitoring_password"
  sensitive   = true
}



# Streaming

variable "source_stream_name" {
  description = ""
}

variable "output_stream_name" {
  description = ""
}

variable "model_bucket" {
  description = "s3_bucket"
}

variable "lambda_function_local_path" {
  description = ""
}

variable "docker_image_local_path" {
  description = ""
}

variable "ecr_repo_name" {
  description = ""
}

variable "lambda_function_name" {
  description = ""
}
