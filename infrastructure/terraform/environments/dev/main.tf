# Development Environment Infrastructure
# AI Manga Generation Service - Minimal Development Setup

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  backend "gcs" {
    bucket = "comic-ai-agent-terraform-state"
    prefix = "environments/dev"
  }
}

# Configure Google Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Local variables
locals {
  environment = "dev"
  common_tags = {
    Environment = local.environment
    Project     = "ai-manga-generation"
    ManagedBy   = "terraform"
  }
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "storage.googleapis.com",
    "servicenetworking.googleapis.com",
    "secretmanager.googleapis.com",
    "compute.googleapis.com",
    "aiplatform.googleapis.com"
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}

# VPC Network (shared with prod for simplicity)
data "google_compute_network" "manga_vpc" {
  name    = "manga-service-vpc"
  project = var.project_id
}

data "google_compute_subnetwork" "manga_private" {
  name    = "manga-private"
  region  = var.region
  project = var.project_id
}

# Service Account for Development
resource "google_service_account" "manga_service_dev" {
  account_id   = "manga-service-dev"
  display_name = "AI Manga Generation Service Account (Dev)"
  project      = var.project_id
}

# IAM roles for development service account
resource "google_project_iam_member" "manga_service_dev_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/redis.editor", 
    "roles/storage.objectAdmin",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.manga_service_dev.email}"
}

# Redis Instance (smaller for dev)
resource "google_redis_instance" "manga_redis_dev" {
  name           = "manga-redis-${local.environment}"
  region         = var.region
  memory_size_gb = var.redis_memory_gb
  tier           = "BASIC"
  redis_version  = "REDIS_7_0"
  
  authorized_network = data.google_compute_network.manga_vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  
  display_name = "AI Manga Generation Redis Cache (Dev)"
  
  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }

  project = var.project_id

  depends_on = [google_project_service.required_apis]
}

# Cloud SQL Module (smaller instance for dev)
module "cloud_sql" {
  source = "../../modules/cloud-sql"

  project_id           = var.project_id
  region              = var.region
  instance_name       = "manga-db-${local.environment}"
  machine_type        = var.db_machine_type
  disk_size_gb        = var.db_disk_size_gb
  max_disk_size_gb    = var.db_max_disk_size_gb
  deletion_protection = var.db_deletion_protection
  vpc_network_id      = data.google_compute_network.manga_vpc.id
  environment         = local.environment
}

# Storage Module (with dev settings)
module "storage" {
  source = "../../modules/storage"

  project_id              = var.project_id
  region                 = var.region
  environment            = local.environment
  force_destroy          = var.storage_force_destroy
  service_account_email  = google_service_account.manga_service_dev.email
  cors_origins           = var.cors_origins
}

# Cloud Run Module (development configuration)
module "cloud_run" {
  source = "../../modules/cloud-run"

  project_id              = var.project_id
  region                 = var.region
  service_name           = "manga-service-${local.environment}"
  container_image        = var.container_image
  environment            = local.environment
  vpc_network            = data.google_compute_network.manga_vpc.name
  subnet_name            = data.google_compute_subnetwork.manga_private.name
  service_account_email  = google_service_account.manga_service_dev.email
  database_url           = module.cloud_sql.database_url
  redis_url              = "redis://${google_redis_instance.manga_redis_dev.host}:${google_redis_instance.manga_redis_dev.port}/0"
  cpu_limit              = var.cloud_run_cpu
  memory_limit           = var.cloud_run_memory
  min_instances          = var.cloud_run_min_instances
  max_instances          = var.cloud_run_max_instances
  concurrency            = var.cloud_run_concurrency
  timeout_seconds        = var.cloud_run_timeout
  allow_unauthenticated  = var.allow_unauthenticated
}

# Development secrets
resource "google_secret_manager_secret" "dev_secrets" {
  for_each = var.application_secrets

  project   = var.project_id
  secret_id = "${each.key}-dev"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "dev_secret_versions" {
  for_each = var.application_secrets

  secret      = google_secret_manager_secret.dev_secrets[each.key].id
  secret_data = each.value
}