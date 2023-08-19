variable "rds_identifier" {
  description = "Name of the RDS instance"
  default     = "postgres"
  type        = string
}

variable "postgres_db_name" {
  description = "Name of the database in the RDS instance"
  default     = "db"
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
