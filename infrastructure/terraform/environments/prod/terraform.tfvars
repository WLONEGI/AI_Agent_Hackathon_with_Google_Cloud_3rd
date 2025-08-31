# Production Environment Configuration
# AI Manga Generation Service

# Project Configuration
project_id = "comic-ai-agent-470309"
region     = "asia-northeast1"

# Database Configuration (Production Specs)
db_machine_type        = "db-custom-1-3840"
db_disk_size_gb        = 100
db_max_disk_size_gb    = 500
db_deletion_protection = true

# Redis Configuration
redis_memory_gb = 1

# Cloud Run Configuration (Production Specs)
container_image           = "gcr.io/comic-ai-agent-470309/manga-service:latest"
cloud_run_cpu            = "1"
cloud_run_memory         = "2Gi"
cloud_run_min_instances  = 1
cloud_run_max_instances  = 50
cloud_run_concurrency    = 50
cloud_run_timeout        = 300
allow_unauthenticated    = true

# Storage Configuration
storage_force_destroy = false
cors_origins = [
  "https://manga-service.com",
  "https://www.manga-service.com",
  "https://app.manga-service.com"
]

# Security Configuration
manga_secret_key = "your-production-secret-key-here"