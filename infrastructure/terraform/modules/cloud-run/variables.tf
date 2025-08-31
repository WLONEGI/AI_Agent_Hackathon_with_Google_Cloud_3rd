# Variables for Cloud Run Module

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
}

variable "container_image" {
  description = "Container image URL"
  type        = string
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

variable "cpu_limit" {
  description = "CPU limit for the service"
  type        = string
  default     = "1"
}

variable "memory_limit" {
  description = "Memory limit for the service"
  type        = string
  default     = "2Gi"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 50
}

variable "concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 50
}

variable "timeout_seconds" {
  description = "Request timeout in seconds"
  type        = number
  default     = 300
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "vpc_network" {
  description = "VPC network name for Direct VPC Egress"
  type        = string
}

variable "subnet_name" {
  description = "Subnet name for Direct VPC Egress"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for the Cloud Run service"
  type        = string
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
}

variable "redis_url" {
  description = "Redis connection URL"
  type        = string
}

variable "secret_key_secret_name" {
  description = "Secret Manager secret name for application secret key"
  type        = string
  default     = "manga-secret-key"
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated requests"
  type        = bool
  default     = true
}

variable "custom_domain" {
  description = "Custom domain for the service (optional)"
  type        = string
  default     = ""
}

# Service-specific overrides for different phases
variable "service_overrides" {
  description = "Service-specific configuration overrides"
  type = object({
    phase5_image = optional(object({
      cpu_limit     = string
      memory_limit  = string
      timeout       = number
      concurrency   = number
    }), {
      cpu_limit     = "2"
      memory_limit  = "4Gi"
      timeout       = 60
      concurrency   = 5
    })
    
    phase2_character = optional(object({
      cpu_limit     = string
      memory_limit  = string
      timeout       = number
    }), {
      cpu_limit     = "1500m"
      memory_limit  = "3Gi"
      timeout       = 20
    })
  })
  default = {}
}