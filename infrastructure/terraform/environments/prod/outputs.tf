# Production Environment Outputs

output "service_url" {
  description = "URL of the deployed manga service"
  value       = module.cloud_run.service_url
}

output "vpc_network_name" {
  description = "VPC network name"
  value       = google_compute_network.manga_vpc.name
}

output "vpc_network_id" {
  description = "VPC network ID"
  value       = google_compute_network.manga_vpc.id
}

output "public_subnet_name" {
  description = "Public subnet name"
  value       = google_compute_subnetwork.manga_public.name
}

output "private_subnet_name" {
  description = "Private subnet name"
  value       = google_compute_subnetwork.manga_private.name
}

output "database_instance_name" {
  description = "Cloud SQL instance name"
  value       = module.cloud_sql.instance_name
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = module.cloud_sql.instance_connection_name
}

output "database_private_ip" {
  description = "Cloud SQL private IP address"
  value       = module.cloud_sql.private_ip_address
}

output "redis_host" {
  description = "Redis instance host"
  value       = google_redis_instance.manga_redis.host
}

output "redis_port" {
  description = "Redis instance port"
  value       = google_redis_instance.manga_redis.port
}

output "storage_buckets" {
  description = "Storage bucket names"
  value       = module.storage.bucket_names
}

output "service_account_email" {
  description = "Service account email"
  value       = google_service_account.manga_service.email
}

output "public_preview_url" {
  description = "Public URL for preview cache"
  value       = module.storage.public_preview_url
}

# Sensitive outputs
output "database_url" {
  description = "Database connection URL"
  value       = module.cloud_sql.database_url
  sensitive   = true
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${google_redis_instance.manga_redis.host}:${google_redis_instance.manga_redis.port}/0"
  sensitive   = true
}