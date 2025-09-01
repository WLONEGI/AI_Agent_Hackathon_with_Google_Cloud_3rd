# CDN Module Variables

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-northeast1"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

# Storage Configuration
variable "preview_bucket_name" {
  description = "Name of the preview cache bucket"
  type        = string
}

variable "images_bucket_name" {
  description = "Name of the output images bucket"
  type        = string
}

variable "final_products_bucket_name" {
  description = "Name of the final products bucket"
  type        = string
}

# Domain Configuration
variable "custom_domain" {
  description = "Custom domain for CDN (optional)"
  type        = string
  default     = ""
}

variable "dns_zone_name" {
  description = "DNS zone name for domain management"
  type        = string
  default     = ""
}

# CDN Configuration
variable "enable_cloud_armor" {
  description = "Enable Cloud Armor security policy"
  type        = bool
  default     = true
}

variable "cache_ttl_seconds" {
  description = "Default cache TTL in seconds"
  type        = number
  default     = 3600
}

variable "max_cache_ttl_seconds" {
  description = "Maximum cache TTL in seconds"
  type        = number
  default     = 86400
}

variable "rate_limit_requests_per_minute" {
  description = "Rate limit: requests per minute per IP"
  type        = number
  default     = 100
}

# Backend Configuration
variable "enable_compression" {
  description = "Enable gzip compression"
  type        = bool
  default     = true
}

variable "compression_types" {
  description = "MIME types to compress"
  type        = list(string)
  default = [
    "text/css",
    "text/javascript",
    "application/javascript",
    "image/svg+xml",
    "text/plain",
    "text/xml",
    "application/json"
  ]
}

# Health Check Configuration
variable "health_check_enabled" {
  description = "Enable health checks for backend services"
  type        = bool
  default     = false  # Cloud Storage doesn't need health checks
}

# Logging Configuration
variable "enable_cdn_logging" {
  description = "Enable CDN access logging"
  type        = bool
  default     = true
}

variable "log_sample_rate" {
  description = "CDN log sampling rate (0.0-1.0)"
  type        = number
  default     = 0.1
}

# Performance Configuration
variable "enable_http2" {
  description = "Enable HTTP/2 support"
  type        = bool
  default     = true
}

variable "connection_draining_timeout" {
  description = "Connection draining timeout in seconds"
  type        = number
  default     = 30
}

# Security Configuration
variable "allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}

variable "blocked_countries" {
  description = "List of country codes to block (ISO 3166-1 alpha-2)"
  type        = list(string)
  default     = []
}

# Cost Optimization
variable "enable_cache_invalidation" {
  description = "Enable cache invalidation capabilities"
  type        = bool
  default     = true
}

variable "cache_invalidation_batch_size" {
  description = "Batch size for cache invalidation"
  type        = number
  default     = 100
}