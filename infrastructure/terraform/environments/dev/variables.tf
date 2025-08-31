# Development Environment Variables

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
  default     = "db-f1-micro"
}

variable "db_disk_size_gb" {
  description = "Initial database disk size in GB"
  type        = number
  default     = 20
}

variable "db_max_disk_size_gb" {
  description = "Maximum database disk size in GB"
  type        = number
  default     = 100
}

variable "db_deletion_protection" {
  description = "Enable deletion protection for database"
  type        = bool
  default     = false
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
  default     = "gcr.io/comic-ai-agent-470309/manga-service:dev"
}

variable "cloud_run_cpu" {
  description = "Cloud Run CPU allocation"
  type        = string
  default     = "1"
}

variable "cloud_run_memory" {
  description = "Cloud Run memory allocation"
  type        = string
  default     = "1Gi"
}

variable "cloud_run_min_instances" {
  description = "Minimum Cloud Run instances"
  type        = number
  default     = 0
}

variable "cloud_run_max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 10
}

variable "cloud_run_concurrency" {
  description = "Cloud Run concurrent requests per instance"
  type        = number
  default     = 10
}

variable "cloud_run_timeout" {
  description = "Cloud Run request timeout in seconds"
  type        = number
  default     = 60
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to Cloud Run service"
  type        = bool
  default     = true
}

# Storage Configuration
variable "storage_force_destroy" {
  description = "Allow storage bucket deletion even if not empty"
  type        = bool
  default     = true
}

variable "cors_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["https://localhost:3000", "https://localhost:*"]
}

# Application Secrets
variable "application_secrets" {
  description = "Application secrets to store in Secret Manager"
  type        = map(string)
  sensitive   = true
  default = {
    manga-secret-key = "dev-secret-key-not-for-production"
  }
}