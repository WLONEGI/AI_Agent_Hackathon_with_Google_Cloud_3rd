# Production Environment Infrastructure
# AI Manga Generation Service - Full Production Setup

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
    prefix = "environments/prod"
  }
}

# Configure Google Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Local variables
locals {
  environment = "prod"
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
    "vpcaccess.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "compute.googleapis.com",
    "aiplatform.googleapis.com"
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}

# VPC Network
resource "google_compute_network" "manga_vpc" {
  name                    = "manga-service-vpc"
  auto_create_subnetworks = false
  mtu                     = 1460
  project                 = var.project_id

  depends_on = [google_project_service.required_apis]
}

# Subnets
resource "google_compute_subnetwork" "manga_public" {
  name          = "manga-public"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.manga_vpc.id
  project       = var.project_id
}

resource "google_compute_subnetwork" "manga_private" {
  name          = "manga-private"
  ip_cidr_range = "10.0.2.0/24"
  region        = var.region
  network       = google_compute_network.manga_vpc.id
  project       = var.project_id
  
  private_ip_google_access = true
  
  secondary_ip_range {
    range_name    = "manga-pods"
    ip_cidr_range = "10.1.0.0/16"
  }
}

# Cloud Router and NAT
resource "google_compute_router" "manga_router" {
  name    = "manga-router"
  region  = var.region
  network = google_compute_network.manga_vpc.id
  project = var.project_id
}

resource "google_compute_router_nat" "manga_nat" {
  name                               = "manga-nat"
  router                             = google_compute_router.manga_router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  project                            = var.project_id
}

# Firewall Rules
resource "google_compute_firewall" "allow_https" {
  name    = "manga-allow-https"
  network = google_compute_network.manga_vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["443", "80"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["https-server"]
}

resource "google_compute_firewall" "allow_internal" {
  name    = "manga-allow-internal"
  network = google_compute_network.manga_vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  source_ranges = ["10.0.0.0/16"]
}

resource "google_compute_firewall" "allow_health_check" {
  name    = "manga-allow-health-check"
  network = google_compute_network.manga_vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["8000", "8080"]
  }

  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = ["cloud-run-service"]
}

# Service Account for Manga Service
resource "google_service_account" "manga_service" {
  account_id   = "manga-service-account"
  display_name = "AI Manga Generation Service Account"
  project      = var.project_id
}

# IAM roles for service account
resource "google_project_iam_member" "manga_service_roles" {
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
  member  = "serviceAccount:${google_service_account.manga_service.email}"
}

# Redis Instance (Memory Store)
resource "google_redis_instance" "manga_redis" {
  name           = "manga-redis-${local.environment}"
  region         = var.region
  memory_size_gb = var.redis_memory_gb
  tier           = "BASIC"
  redis_version  = "REDIS_7_0"
  
  authorized_network = google_compute_network.manga_vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  
  display_name = "AI Manga Generation Redis Cache"
  
  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }

  project = var.project_id

  depends_on = [google_project_service.required_apis]
}

# Cloud SQL Module
module "cloud_sql" {
  source = "../../modules/cloud-sql"

  project_id           = var.project_id
  region              = var.region
  instance_name       = "manga-db-${local.environment}"
  machine_type        = var.db_machine_type
  disk_size_gb        = var.db_disk_size_gb
  max_disk_size_gb    = var.db_max_disk_size_gb
  deletion_protection = var.db_deletion_protection
  vpc_network_id      = google_compute_network.manga_vpc.id
  environment         = local.environment
}

# Storage Module
module "storage" {
  source = "../../modules/storage"

  project_id              = var.project_id
  region                 = var.region
  environment            = local.environment
  force_destroy          = var.storage_force_destroy
  service_account_email  = google_service_account.manga_service.email
  cors_origins           = var.cors_origins
}

# Backend Cloud Run Module
module "backend_cloud_run" {
  source = "../../modules/cloud-run"

  project_id              = var.project_id
  region                 = var.region
  service_name           = "manga-backend-${local.environment}"
  container_image        = var.backend_container_image
  environment            = local.environment
  vpc_network            = google_compute_network.manga_vpc.name
  subnet_name            = google_compute_subnetwork.manga_private.name
  service_account_email  = google_service_account.manga_service.email
  database_url           = module.cloud_sql.database_url
  redis_url              = "redis://${google_redis_instance.manga_redis.host}:${google_redis_instance.manga_redis.port}/0"
  cpu_limit              = var.backend_cpu_limit
  memory_limit           = var.backend_memory_limit
  min_instances          = var.backend_min_instances
  max_instances          = var.backend_max_instances
  concurrency            = var.backend_concurrency
  timeout_seconds        = var.backend_timeout
  allow_unauthenticated  = var.allow_unauthenticated
  custom_domain          = var.backend_custom_domain
}

# Frontend Cloud Run Module
module "frontend_cloud_run" {
  source = "../../modules/frontend-cloud-run"

  project_id              = var.project_id
  region                 = var.region
  service_name           = "manga-frontend-${local.environment}"
  container_image        = var.frontend_container_image
  environment            = local.environment
  service_account_email  = google_service_account.manga_service.email
  backend_url            = module.backend_cloud_run.service_url
  cpu_limit              = var.frontend_cpu_limit
  memory_limit           = var.frontend_memory_limit
  min_instances          = var.frontend_min_instances
  max_instances          = var.frontend_max_instances
  concurrency            = var.frontend_concurrency
  timeout_seconds        = var.frontend_timeout
  custom_domain          = var.frontend_custom_domain
}

# CDN Module for Global Image Delivery
module "cdn" {
  source = "../../modules/cdn"

  project_id                = var.project_id
  region                   = var.region
  environment              = local.environment
  
  # Storage buckets
  preview_bucket_name      = module.storage.bucket_names.preview_cache
  images_bucket_name       = module.storage.bucket_names.output_images
  final_products_bucket_name = module.storage.bucket_names.final_products
  
  # Domain configuration
  custom_domain           = var.cdn_custom_domain
  dns_zone_name          = var.dns_zone_name
  
  # CDN performance settings
  cache_ttl_seconds       = var.cdn_cache_ttl
  max_cache_ttl_seconds   = var.cdn_max_cache_ttl
  enable_compression      = var.cdn_enable_compression
  
  # Security settings
  enable_cloud_armor      = var.cdn_enable_cloud_armor
  rate_limit_requests_per_minute = var.cdn_rate_limit_rpm
  allowed_origins         = var.cors_origins
  
  # Performance optimization
  enable_http2           = true
  enable_cdn_logging     = var.cdn_enable_logging
  log_sample_rate       = var.cdn_log_sample_rate

  depends_on = [module.storage]
}

# Secret Manager secrets
resource "google_secret_manager_secret" "manga_secret_key" {
  project   = var.project_id
  secret_id = "manga-secret-key"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "manga_secret_key_version" {
  secret      = google_secret_manager_secret.manga_secret_key.id
  secret_data = var.manga_secret_key
}