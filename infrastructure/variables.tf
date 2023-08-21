# General Configuration
variable "aws_region" {
  description = "AWS region to create resources"
  default     = "us-east-1"
}

variable "project_id" {
  description = "Unique identifier for the project"
  default     = "mlops-xgoals"
}

# MLflow RDS Configuration
variable "mlflow_rds_identifier" {
  description = "The identifier for the MLflow RDS instance"
  default     = "mlflow-db"
}

variable "mlflow_postgres_db_name" {
  description = "The name of the default database for MLflow"
  default     = "mlflow_db"
}

variable "mlflow_postgres_db_username" {
  description = "Username for the MLflow RDS database"
  default     = "mlflow_user"
}

variable "mlflow_postgres_db_password" {
  description = "Password for the MLflow RDS database"
  default     = "mlflow_password"
  sensitive   = true
}

# Model Monitoring RDS Configuration
variable "monitoring_rds_identifier" {
  description = "The identifier for the model monitoring RDS instance"
  default     = "model-monitoring-db"
}

variable "monitoring_postgres_db_name" {
  description = "The name of the default database for model monitoring"
  default     = "model-monitoring"
}

variable "monitoring_postgres_db_username" {
  description = "Username for the model monitoring RDS database"
  default     = "monitoringuser"
}

variable "monitoring_postgres_db_password" {
  description = "Password for the model monitoring RDS database"
  default     = "monitoringpassword"
  sensitive   = true
}

# Streaming Configuration
variable "source_stream_name" {
  description = "Name of the source Kinesis stream"
}

variable "output_stream_name" {
  description = "Name of the output Kinesis stream"
}

# S3 and ECR Configuration
variable "model_bucket" {
  description = "Name of the S3 bucket for storing models"
}

variable "lambda_function_local_path" {
  description = "Local path to the Lambda function code"
}

variable "docker_image_local_path" {
  description = "Local path to the Docker image for the Lambda function"
}

variable "ecr_repo_name" {
  description = "Name of the ECR repository for storing Docker images"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
}
