# Cloud Run Service Module for AI Manga Generation Service
# Implements Direct VPC Egress configuration as per infrastructure design

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Main Cloud Run Service
resource "google_cloud_run_v2_service" "manga_service" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    annotations = {
      "run.googleapis.com/execution-environment" = "gen2"
      "run.googleapis.com/cpu-throttling"        = "false"
    }

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    vpc_access {
      # Direct VPC Egress configuration (no VPC Connector needed)
      network_interfaces {
        network    = var.vpc_network
        subnetwork = var.subnet_name
        tags       = ["cloud-run-service"]
      }
      egress = "ALL_TRAFFIC"
    }

    containers {
      image = var.container_image
      
      ports {
        container_port = var.container_port
      }

      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        cpu_idle = true
        startup_cpu_boost = true
      }

      env {
        name  = "ENV"
        value = var.environment
      }

      env {
        name  = "DATABASE_URL"
        value = var.database_url
      }

      env {
        name  = "REDIS_URL"
        value = var.redis_url
      }

      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_key_secret_name
            version = "latest"
          }
        }
      }

      env {
        name = "GOOGLE_APPLICATION_CREDENTIALS"
        value = "/app/service-account.json"
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "FIREBASE_PROJECT_ID"
        value = var.project_id
      }

      startup_probe {
        http_get {
          path = "/health"
          port = var.container_port
        }
        initial_delay_seconds = 30
        timeout_seconds       = 10
        period_seconds        = 15
        failure_threshold     = 5
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = var.container_port
        }
        initial_delay_seconds = 30
        timeout_seconds       = 5
        period_seconds        = 30
        failure_threshold     = 3
      }
    }

    service_account = var.service_account_email
    timeout         = "${var.timeout_seconds}s"

    max_instance_request_concurrency = var.concurrency
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_project_service.cloud_run
  ]
}

# Enable Cloud Run API
resource "google_project_service" "cloud_run" {
  project = var.project_id
  service = "run.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

# IAM policy for invoking the service
resource "google_cloud_run_v2_service_iam_binding" "invoker" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.manga_service.name
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}

# Custom domain mapping (if provided)
resource "google_cloud_run_domain_mapping" "domain" {
  count = var.custom_domain != "" ? 1 : 0

  location = var.region
  name     = var.custom_domain
  project  = var.project_id

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.manga_service.name
  }
}