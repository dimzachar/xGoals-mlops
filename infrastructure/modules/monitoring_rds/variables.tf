variable "allocated_storage" {
  description = "The allocated storage size for the RDS instance in GB"
  type        = number
  default     = 20
}

variable "instance_class" {
  description = "The instance type of the RDS instance"
  type        = string
  default     = "db.t3.micro"
}

variable "monitoring_postgres_db_name" {
  description = "The name of the default database to create"
  type        = string
}

variable "monitoring_postgres_db_username" {
  description = "Username for the master DB user"
  type        = string
}

variable "monitoring_postgres_db_password" {
  description = "Password for the master DB user"
  type        = string
  sensitive   = true
}
