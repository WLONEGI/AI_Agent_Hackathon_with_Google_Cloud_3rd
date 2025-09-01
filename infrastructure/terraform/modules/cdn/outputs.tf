# CDN Module Outputs

# IP Addresses
output "global_ip_address" {
  description = "Global external IP address for CDN"
  value       = google_compute_global_address.cdn_ip.address
}

output "global_ip_name" {
  description = "Global external IP resource name"
  value       = google_compute_global_address.cdn_ip.name
}

# Domain and URLs
output "cdn_domain" {
  description = "CDN domain (custom domain or IP)"
  value       = var.custom_domain != "" ? var.custom_domain : google_compute_global_address.cdn_ip.address
}

output "preview_cdn_url" {
  description = "CDN URL for preview content"
  value       = var.custom_domain != "" ? "https://${var.custom_domain}/preview" : "https://${google_compute_global_address.cdn_ip.address}/preview"
}

output "images_cdn_url" {
  description = "CDN URL for output images"
  value       = var.custom_domain != "" ? "https://${var.custom_domain}/images" : "https://${google_compute_global_address.cdn_ip.address}/images"
}

# SSL Configuration
output "ssl_certificate_name" {
  description = "Managed SSL certificate name"
  value       = var.custom_domain != "" ? google_compute_managed_ssl_certificate.cdn_ssl[0].name : null
}

output "ssl_certificate_status" {
  description = "SSL certificate provisioning status"
  value       = var.custom_domain != "" ? "provisioning" : null
}

# Backend Services
output "preview_backend_name" {
  description = "Preview backend service name"
  value       = google_compute_backend_bucket.preview_backend.name
}

output "images_backend_name" {
  description = "Images backend service name"
  value       = google_compute_backend_bucket.images_backend.name
}

# Load Balancer Components
output "url_map_name" {
  description = "URL map name"
  value       = google_compute_url_map.cdn_url_map.name
}

output "https_proxy_name" {
  description = "HTTPS proxy name"
  value       = var.custom_domain != "" ? google_compute_target_https_proxy.cdn_https_proxy[0].name : null
}

output "http_proxy_name" {
  description = "HTTP proxy name"
  value       = google_compute_target_http_proxy.cdn_http_proxy.name
}

# Security
output "security_policy_name" {
  description = "Cloud Armor security policy name"
  value       = google_compute_security_policy.cdn_security_policy.name
}

# Configuration Summary
output "cdn_configuration" {
  description = "CDN configuration summary"
  value = {
    global_ip        = google_compute_global_address.cdn_ip.address
    custom_domain    = var.custom_domain
    ssl_enabled      = var.custom_domain != ""
    cache_ttl        = var.cache_ttl_seconds
    max_cache_ttl    = var.max_cache_ttl_seconds
    compression      = var.enable_compression
    security_policy  = var.enable_cloud_armor
    environment      = var.environment
  }
}

# Backend Service Details
output "backend_services" {
  description = "Backend service configuration"
  value = {
    preview = {
      name   = google_compute_backend_bucket.preview_backend.name
      bucket = var.preview_bucket_name
      ttl    = google_compute_backend_bucket.preview_backend.cdn_policy[0].default_ttl
    }
    images = {
      name   = google_compute_backend_bucket.images_backend.name
      bucket = var.images_bucket_name
      ttl    = google_compute_backend_bucket.images_backend.cdn_policy[0].default_ttl
    }
  }
}

# Performance Metrics (for monitoring)
output "performance_config" {
  description = "Performance configuration for monitoring"
  value = {
    cache_mode           = "CACHE_ALL_STATIC"
    compression_enabled  = var.enable_compression
    http2_enabled       = var.enable_http2
    logging_enabled     = var.enable_cdn_logging
    log_sample_rate     = var.log_sample_rate
  }
}