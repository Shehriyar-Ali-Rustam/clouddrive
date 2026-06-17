# ---- Useful values printed after `terraform apply` ----

output "app_url" {
  description = "Open this in your browser once the image is pushed and tasks are healthy"
  value       = "http://${aws_lb.main.dns_name}"
}

output "ecr_repository_url" {
  description = "docker push target for the API image"
  value       = aws_ecr_repository.api.repository_url
}

output "s3_bucket" {
  value = aws_s3_bucket.files.bucket
}

output "rds_endpoint" {
  value = aws_db_instance.metadata.address
}

output "ecs_cluster" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service" {
  value = aws_ecs_service.api.name
}
