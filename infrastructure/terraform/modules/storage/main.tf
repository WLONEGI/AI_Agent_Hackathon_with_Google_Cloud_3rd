# Cloud Storage Module for AI Manga Generation Service
# Multiple buckets with lifecycle and CORS configuration

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Enable Cloud Storage API
resource "google_project_service" "storage" {
  project = var.project_id
  service = "storage.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Input Data Bucket
resource "google_storage_bucket" "manga_input_data" {
  name     = "${var.project_id}-manga-input-data"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true
  force_destroy               = var.force_destroy

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.storage]
}

# Output Images Bucket
resource "google_storage_bucket" "manga_output_images" {
  name     = "${var.project_id}-manga-output-images"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true
  force_destroy               = var.force_destroy

  cors {
    origin          = var.cors_origins
    method          = ["GET", "HEAD", "PUT", "POST"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  depends_on = [google_project_service.storage]
}

# Preview Cache Bucket (with public access)
resource "google_storage_bucket" "manga_preview_cache" {
  name     = "${var.project_id}-manga-preview-cache"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true
  force_destroy               = var.force_destroy

  cors {
    origin          = var.cors_origins
    method          = ["GET", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.storage]
}

# Version Snapshots Bucket
resource "google_storage_bucket" "manga_version_snapshots" {
  name     = "${var.project_id}-manga-version-snapshots"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true
  force_destroy               = var.force_destroy

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 60
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.storage]
}

# Final Products Bucket (long-term storage)
resource "google_storage_bucket" "manga_final_products" {
  name     = "${var.project_id}-manga-final-products"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true
  force_destroy               = var.force_destroy

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  depends_on = [google_project_service.storage]
}

# Temporary Data Bucket
resource "google_storage_bucket" "manga_temp_data" {
  name     = "${var.project_id}-manga-temp-data"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true
  force_destroy               = true

  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.storage]
}

# IAM for manga service account
resource "google_storage_bucket_iam_member" "manga_service_object_admin" {
  for_each = toset([
    google_storage_bucket.manga_input_data.name,
    google_storage_bucket.manga_output_images.name,
    google_storage_bucket.manga_preview_cache.name,
    google_storage_bucket.manga_version_snapshots.name,
    google_storage_bucket.manga_final_products.name,
    google_storage_bucket.manga_temp_data.name
  ])

  bucket = each.value
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.service_account_email}"
}

# Public access for preview cache (if enabled)
resource "google_storage_bucket_iam_member" "preview_public_access" {
  count = var.enable_public_preview_access ? 1 : 0

  bucket = google_storage_bucket.manga_preview_cache.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}