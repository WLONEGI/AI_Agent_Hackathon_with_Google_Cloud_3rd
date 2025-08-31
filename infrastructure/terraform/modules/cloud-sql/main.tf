# Cloud SQL Module for AI Manga Generation Service
# PostgreSQL 15 with private IP configuration

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Store database password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  project   = var.project_id
  secret_id = var.db_password_secret_name
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Enable required APIs
resource "google_project_service" "sqladmin" {
  project = var.project_id
  service = "sqladmin.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

resource "google_project_service" "servicenetworking" {
  project = var.project_id
  service = "servicenetworking.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Use existing private IP range for Google services
data "google_compute_global_address" "private_ip_range" {
  project = var.project_id
  name    = "google-managed-services-manga-service-vpc"
}

# Cloud SQL Instance
resource "google_sql_database_instance" "manga_db" {
  project             = var.project_id
  name                = var.instance_name
  database_version    = "POSTGRES_15"
  region              = var.region
  deletion_protection = var.deletion_protection

  settings {
    tier                        = var.machine_type
    disk_type                   = "PD_SSD"
    disk_size                   = var.disk_size_gb
    disk_autoresize             = true
    disk_autoresize_limit       = var.max_disk_size_gb
    availability_type           = var.availability_type
    deletion_protection_enabled = var.deletion_protection


    backup_configuration {
      enabled                        = true
      start_time                     = "20:00"  # 03:00 JST
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = var.backup_retention_days
      }
      transaction_log_retention_days = 7
    }

    maintenance_window {
      day         = 7  # Sunday
      hour        = 19 # 04:00 JST
      update_track = "stable"
    }

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = var.vpc_network_id
      enable_private_path_for_google_cloud_services = true
      ssl_mode                                      = "ENCRYPTED_ONLY"
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }

    location_preference {
      zone = var.preferred_zone
    }
  }

  depends_on = [
    google_project_service.sqladmin
  ]
}

# Create database
resource "google_sql_database" "manga_database" {
  project  = var.project_id
  name     = var.database_name
  instance = google_sql_database_instance.manga_db.name
}

# Create database user
resource "google_sql_user" "manga_user" {
  project  = var.project_id
  name     = var.db_username
  instance = google_sql_database_instance.manga_db.name
  password = random_password.db_password.result
}

# Create read-only user for monitoring
resource "google_sql_user" "readonly_user" {
  project  = var.project_id
  name     = "${var.db_username}_readonly"
  instance = google_sql_database_instance.manga_db.name
  password = random_password.db_password.result
}

# SSL Certificate
resource "google_sql_ssl_cert" "client_cert" {
  project     = var.project_id
  common_name = "manga-ssl-cert"
  instance    = google_sql_database_instance.manga_db.name
}