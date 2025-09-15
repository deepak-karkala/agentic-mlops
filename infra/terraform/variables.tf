variable "region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project prefix for resource names"
  type        = string
  default     = "agentic-mlops"
}

variable "artifact_bucket_name" {
  description = "Name of the S3 bucket for artifacts"
  type        = string
}

variable "api_image" {
  description = "ECR image identifier for API service"
  type        = string
  default     = ""
}

# worker_image variable removed - worker is now integrated into API service

variable "frontend_image" {
  description = "ECR image identifier for frontend service"
  type        = string
  default     = ""
}

variable "db_username" {
  description = "Username for RDS Postgres"
  type        = string
}

variable "db_password" {
  description = "Password for RDS Postgres"
  type        = string
  sensitive   = true
}

variable "vpc_id" {
  description = "VPC ID for RDS and App Runner"
  type        = string
  default     = null
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
  default     = []
}
