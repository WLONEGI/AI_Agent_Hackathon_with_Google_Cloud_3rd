# Variables for Frontend Cloud Run Service Module

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for deployment"
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

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "service_account_email" {
  description = "Service account email for the Cloud Run service"
  type        = string
}

variable "backend_url" {
  description = "Backend API URL for frontend to connect"
  type        = string
}

variable "cpu_limit" {
  description = "CPU limit for the container"
  type        = string
  default     = "1"
}

variable "memory_limit" {
  description = "Memory limit for the container"
  type        = string
  default     = "512Mi"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "concurrency" {
  description = "Maximum number of concurrent requests per instance"
  type        = number
  default     = 80
}

variable "timeout_seconds" {
  description = "Request timeout in seconds"
  type        = number
  default     = 300
}

variable "custom_domain" {
  description = "Custom domain for the service (optional)"
  type        = string
  default     = ""
}