# Frontend Cloud Run Service Module for AI Manga Generation Service
# Next.js application deployment to Cloud Run

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Frontend Cloud Run Service
resource "google_cloud_run_v2_service" "frontend_service" {
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

    containers {
      image = var.container_image
      
      ports {
        container_port = 3000
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
        name  = "NODE_ENV"
        value = "production"
      }

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = var.backend_url
      }

      env {
        name  = "NEXT_TELEMETRY_DISABLED"
        value = "1"
      }


      env {
        name  = "HOSTNAME"
        value = "0.0.0.0"
      }

      startup_probe {
        http_get {
          path = "/api/health"
          port = 3000
        }
        initial_delay_seconds = 60
        timeout_seconds       = 30
        period_seconds        = 10
        failure_threshold     = 6
      }

      liveness_probe {
        http_get {
          path = "/api/health"
          port = 3000
        }
        initial_delay_seconds = 60
        timeout_seconds       = 15
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

# IAM policy for invoking the service (public access for frontend)
resource "google_cloud_run_v2_service_iam_binding" "invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend_service.name
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
    route_name = google_cloud_run_v2_service.frontend_service.name
  }
}