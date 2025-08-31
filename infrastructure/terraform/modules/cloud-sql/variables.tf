# Variables for Cloud SQL Module

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "preferred_zone" {
  description = "Preferred zone within the region"
  type        = string
  default     = "asia-northeast1-a"
}

variable "instance_name" {
  description = "Name of the Cloud SQL instance"
  type        = string
}

variable "machine_type" {
  description = "Machine type for the Cloud SQL instance"
  type        = string
  default     = "db-standard-1"
}

variable "disk_size_gb" {
  description = "Initial disk size in GB"
  type        = number
  default     = 100
}

variable "max_disk_size_gb" {
  description = "Maximum disk size in GB for auto-resize"
  type        = number
  default     = 500
}

variable "availability_type" {
  description = "Availability type (ZONAL or REGIONAL)"
  type        = string
  default     = "ZONAL"
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = "manga_db"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "manga_user"
}

variable "db_password_secret_name" {
  description = "Secret Manager secret name for database password"
  type        = string
  default     = "manga-db-password"
}

variable "vpc_network_id" {
  description = "VPC network ID for private IP configuration"
  type        = string
}


variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}