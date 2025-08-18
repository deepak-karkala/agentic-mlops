output "api_service_url" {
  description = "URL of the API App Runner service"
  value       = aws_apprunner_service.api.service_url
}

output "worker_service_url" {
  description = "URL of the Worker App Runner service"
  value       = aws_apprunner_service.worker.service_url
}

output "db_endpoint" {
  description = "Endpoint of the Postgres instance"
  value       = aws_db_instance.postgres.endpoint
}

output "s3_bucket_name" {
  description = "Artifacts S3 bucket name"
  value       = aws_s3_bucket.artifacts.bucket
}
