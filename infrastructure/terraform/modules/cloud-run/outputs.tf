# Outputs for Cloud Run Module

output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.manga_service.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.manga_service.name
}

output "service_id" {
  description = "Full resource ID of the Cloud Run service"
  value       = google_cloud_run_v2_service.manga_service.id
}

output "service_location" {
  description = "Location of the Cloud Run service"
  value       = google_cloud_run_v2_service.manga_service.location
}

output "domain_mapping_status" {
  description = "Status of custom domain mapping (if configured)"
  value       = var.custom_domain != "" ? google_cloud_run_domain_mapping.domain[0].status : null
}

output "latest_revision" {
  description = "Latest revision of the service"
  value       = google_cloud_run_v2_service.manga_service.latest_ready_revision
}

output "ingress_status" {
  description = "Ingress configuration status"
  value = {
    traffic_percent = google_cloud_run_v2_service.manga_service.traffic[0].percent
    revision        = google_cloud_run_v2_service.manga_service.traffic[0].revision
  }
}