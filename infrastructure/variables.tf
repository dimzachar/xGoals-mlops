# variable "aws_region" {
#   description = "AWS region to create resources"
#   default     = "us-east-1"
# }

# variable "project_id" {
#   description = "project_id"
#   default = "mlops-xgoals"
# }

variable "rds_identifier" {
  description = "Name of the RDS instance"
  default     = "mlflow-database-postgres"
  type        = string
}

variable "postgres_db_name" {
  description = "Name of the database in the RDS instance"
  default     = "db_postgres"
  type        = string
}

variable "postgres_db_username" {
  description = "Username for the RDS database"
  default     = "db_user"
  type        = string
}

variable "postgres_db_password" {
  description = "Password for the RDS database"
  type        = string
  default     = "db_password"
  sensitive   = true
}


# variable "source_stream_name" {
#   description = ""
# }

# variable "output_stream_name" {
#   description = ""
# }

# variable "model_bucket" {
#   description = "s3_bucket"
# }

# variable "lambda_function_local_path" {
#   description = ""
# }

# variable "docker_image_local_path" {
#   description = ""
# }

# variable "ecr_repo_name" {
#   description = ""
# }

# variable "lambda_function_name" {
#   description = ""
# }
