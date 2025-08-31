# Variables for Storage Module

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "force_destroy" {
  description = "Allow bucket deletion even if not empty (use carefully in production)"
  type        = bool
  default     = false
}

variable "cors_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["https://*.manga-service.com", "https://localhost:*"]
}

variable "service_account_email" {
  description = "Service account email for bucket access"
  type        = string
}

variable "enable_public_preview_access" {
  description = "Enable public access to preview cache bucket"
  type        = bool
  default     = true
}