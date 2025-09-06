output "api_service_url" {
  description = "URL of the API App Runner service"
  value       = length(aws_apprunner_service.api) > 0 ? aws_apprunner_service.api[0].service_url : "Not deployed yet - run phase 3"
}

output "worker_service_url" {
  description = "URL of the Worker App Runner service"
  value       = length(aws_apprunner_service.worker) > 0 ? aws_apprunner_service.worker[0].service_url : "Not deployed yet - run phase 3"
}

output "frontend_service_url" {
  description = "URL of the Frontend App Runner service"
  value       = length(aws_apprunner_service.frontend) > 0 ? aws_apprunner_service.frontend[0].service_url : "Not deployed yet - run phase 3"
}

output "db_endpoint" {
  description = "Endpoint of the Postgres instance"
  value       = aws_db_instance.postgres.endpoint
}

output "s3_bucket_name" {
  description = "Artifacts S3 bucket name"
  value       = aws_s3_bucket.artifacts.bucket
}

output "db_proxy_endpoint" {
  description = "RDS Proxy endpoint"
  value       = aws_db_proxy.postgres.endpoint
}

output "secrets_manager_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "api_ecr_repository_url" {
  description = "URL of the API ECR repository"
  value       = aws_ecr_repository.api.repository_url
}

output "worker_ecr_repository_url" {
  description = "URL of the Worker ECR repository"
  value       = aws_ecr_repository.worker.repository_url
}

output "frontend_ecr_repository_url" {
  description = "URL of the Frontend ECR repository"
  value       = aws_ecr_repository.frontend.repository_url
}
