# Development Environment Configuration
# AI Manga Generation Service

# Project Configuration
project_id = "comic-ai-agent-470309"
region     = "asia-northeast1"

# Database Configuration (Smaller for dev)
db_machine_type        = "db-f1-micro"
db_disk_size_gb        = 20
db_max_disk_size_gb    = 100
db_deletion_protection = false

# Redis Configuration (Smaller for dev)
redis_memory_gb = 1

# Cloud Run Configuration (Development)
container_image           = "gcr.io/comic-ai-agent-470309/manga-service:dev"
cloud_run_cpu            = "1"
cloud_run_memory         = "1Gi"
cloud_run_min_instances  = 0
cloud_run_max_instances  = 10
cloud_run_concurrency    = 10
cloud_run_timeout        = 60
allow_unauthenticated    = true

# Storage Configuration (Allow deletion for dev)
storage_force_destroy = true
cors_origins = [
  "https://localhost:3000",
  "https://localhost:*",
  "https://*.manga-service.com"
]

# Security Configuration (Development)
application_secrets = {
  "manga-secret-key" = "dev-secret-key-not-for-production"
}