# Outputs for Frontend Cloud Run Service Module

output "service_name" {
  description = "Name of the deployed service"
  value       = google_cloud_run_v2_service.frontend_service.name
}

output "service_url" {
  description = "URL of the deployed frontend service"
  value       = google_cloud_run_v2_service.frontend_service.uri
}

output "service_id" {
  description = "ID of the deployed service"
  value       = google_cloud_run_v2_service.frontend_service.id
}

output "custom_domain_url" {
  description = "Custom domain URL (if configured)"
  value       = var.custom_domain != "" ? "https://${var.custom_domain}" : ""
}