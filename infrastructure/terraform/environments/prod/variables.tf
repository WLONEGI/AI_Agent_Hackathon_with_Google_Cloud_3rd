# Production Environment Variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "comic-ai-agent-470309"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

# Database Configuration
variable "db_machine_type" {
  description = "Cloud SQL machine type"
  type        = string
  default     = "db-standard-1"
}

variable "db_disk_size_gb" {
  description = "Initial database disk size in GB"
  type        = number
  default     = 100
}

variable "db_max_disk_size_gb" {
  description = "Maximum database disk size in GB"
  type        = number
  default     = 500
}

variable "db_deletion_protection" {
  description = "Enable deletion protection for database"
  type        = bool
  default     = true
}

# Redis Configuration
variable "redis_memory_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

# Cloud Run Configuration
variable "container_image" {
  description = "Container image for Cloud Run"
  type        = string
  default     = "gcr.io/comic-ai-agent-470309/manga-service:latest"
}

variable "cloud_run_cpu" {
  description = "Cloud Run CPU allocation"
  type        = string
  default     = "1"
}

variable "cloud_run_memory" {
  description = "Cloud Run memory allocation"
  type        = string
  default     = "2Gi"
}

variable "cloud_run_min_instances" {
  description = "Minimum Cloud Run instances"
  type        = number
  default     = 1
}

variable "cloud_run_max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 50
}

variable "cloud_run_concurrency" {
  description = "Cloud Run concurrent requests per instance"
  type        = number
  default     = 50
}

variable "cloud_run_timeout" {
  description = "Cloud Run request timeout in seconds"
  type        = number
  default     = 300
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to Cloud Run service"
  type        = bool
  default     = true
}

variable "custom_domain" {
  description = "Custom domain for the service"
  type        = string
  default     = ""
}

# Storage Configuration
variable "storage_force_destroy" {
  description = "Allow storage bucket deletion even if not empty"
  type        = bool
  default     = false
}

variable "cors_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["https://*.manga-service.com"]
}

# CDN Configuration
variable "cdn_custom_domain" {
  description = "Custom domain for CDN (optional)"
  type        = string
  default     = ""
}

variable "dns_zone_name" {
  description = "Cloud DNS zone name for domain management"
  type        = string
  default     = ""
}

variable "cdn_cache_ttl" {
  description = "CDN default cache TTL in seconds"
  type        = number
  default     = 3600  # 1 hour
}

variable "cdn_max_cache_ttl" {
  description = "CDN maximum cache TTL in seconds"
  type        = number
  default     = 86400  # 24 hours
}

variable "cdn_enable_compression" {
  description = "Enable CDN compression"
  type        = bool
  default     = true
}

variable "cdn_enable_cloud_armor" {
  description = "Enable Cloud Armor security policy"
  type        = bool
  default     = true
}

variable "cdn_rate_limit_rpm" {
  description = "CDN rate limit requests per minute per IP"
  type        = number
  default     = 100
}

variable "cdn_enable_logging" {
  description = "Enable CDN access logging"
  type        = bool
  default     = true
}

variable "cdn_log_sample_rate" {
  description = "CDN log sampling rate (0.0-1.0)"
  type        = number
  default     = 0.1
}

# Application Secrets
variable "manga_secret_key" {
  description = "Secret key for the manga application"
  type        = string
  sensitive   = true
  default     = "production-secret-key-replace-this"
}