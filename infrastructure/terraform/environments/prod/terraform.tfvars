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

# Backend Cloud Run Configuration (Production Specs)
backend_container_image    = "asia-northeast1-docker.pkg.dev/comic-ai-agent-470309/manga-service/backend:latest"
backend_cpu_limit         = "2"
backend_memory_limit      = "2Gi"
backend_min_instances     = 1
backend_max_instances     = 50
backend_concurrency       = 50
backend_timeout          = 900

# Frontend Cloud Run Configuration (Production Specs)
frontend_container_image   = "asia-northeast1-docker.pkg.dev/comic-ai-agent-470309/manga-service/frontend:latest"
frontend_cpu_limit        = "1"
frontend_memory_limit     = "512Mi"
frontend_min_instances    = 0
frontend_max_instances    = 10
frontend_concurrency      = 80
frontend_timeout         = 300
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