# Cloud CDN Module for AI Manga Generation Service
# Global Load Balancer + Cloud CDN for optimized image delivery

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Enable Compute API (required for Load Balancer)
resource "google_project_service" "compute" {
  project = var.project_id
  service = "compute.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Global External IP Address
resource "google_compute_global_address" "cdn_ip" {
  name    = "manga-cdn-global-ip"
  project = var.project_id

  depends_on = [google_project_service.compute]
}

# Managed SSL Certificate
resource "google_compute_managed_ssl_certificate" "cdn_ssl" {
  count = var.custom_domain != "" ? 1 : 0
  
  name    = "manga-cdn-ssl-cert"
  project = var.project_id

  managed {
    domains = [var.custom_domain]
  }

  depends_on = [google_project_service.compute]
}

# Backend Service for Preview Cache (Public Access)
resource "google_compute_backend_bucket" "preview_backend" {
  name        = "manga-preview-backend"
  project     = var.project_id
  bucket_name = var.preview_bucket_name
  description = "CDN backend for manga preview cache"
  
  enable_cdn = true
  
  cdn_policy {
    cache_mode       = "CACHE_ALL_STATIC"
    default_ttl      = 3600  # 1 hour
    max_ttl          = 86400 # 24 hours
    client_ttl       = 3600  # 1 hour
    negative_caching = true
  }

  depends_on = [google_project_service.compute]
}

# Backend Service for Output Images (Signed URLs)
resource "google_compute_backend_bucket" "images_backend" {
  name        = "manga-images-backend"
  project     = var.project_id
  bucket_name = var.images_bucket_name
  description = "CDN backend for manga output images"
  
  enable_cdn = true
  
  cdn_policy {
    cache_mode       = "CACHE_ALL_STATIC"
    default_ttl      = 7200  # 2 hours (longer for final images)
    max_ttl          = 604800 # 7 days
    client_ttl       = 7200  # 2 hours
    negative_caching = true
  }

  depends_on = [google_project_service.compute]
}

# URL Map for routing
resource "google_compute_url_map" "cdn_url_map" {
  name            = "manga-cdn-url-map"
  project         = var.project_id
  default_service = google_compute_backend_bucket.preview_backend.id
  description     = "URL mapping for manga CDN"

  host_rule {
    hosts        = var.custom_domain != "" ? [var.custom_domain] : ["*"]
    path_matcher = "manga-paths"
  }

  path_matcher {
    name            = "manga-paths"
    default_service = google_compute_backend_bucket.preview_backend.id

    # Preview images (public access)
    path_rule {
      paths   = ["/preview/*", "/thumbnails/*", "/cache/*"]
      service = google_compute_backend_bucket.preview_backend.id
    }

    # Generated images (signed URLs)
    path_rule {
      paths   = ["/images/*", "/output/*", "/generated/*"]
      service = google_compute_backend_bucket.images_backend.id
    }
  }

  depends_on = [google_project_service.compute]
}

# HTTPS Proxy
resource "google_compute_target_https_proxy" "cdn_https_proxy" {
  count = var.custom_domain != "" ? 1 : 0
  
  name    = "manga-cdn-https-proxy"
  project = var.project_id
  url_map = google_compute_url_map.cdn_url_map.id
  
  ssl_certificates = [google_compute_managed_ssl_certificate.cdn_ssl[0].id]

  depends_on = [google_project_service.compute]
}

# HTTP Proxy (redirect to HTTPS)
resource "google_compute_target_http_proxy" "cdn_http_proxy" {
  name    = "manga-cdn-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.cdn_url_map.id

  depends_on = [google_project_service.compute]
}

# Global Forwarding Rule (HTTPS)
resource "google_compute_global_forwarding_rule" "cdn_https_forwarding_rule" {
  count = var.custom_domain != "" ? 1 : 0
  
  name       = "manga-cdn-https-forwarding-rule"
  project    = var.project_id
  target     = google_compute_target_https_proxy.cdn_https_proxy[0].id
  port_range = "443"
  ip_address = google_compute_global_address.cdn_ip.address

  depends_on = [google_project_service.compute]
}

# Global Forwarding Rule (HTTP - redirect to HTTPS)
resource "google_compute_global_forwarding_rule" "cdn_http_forwarding_rule" {
  name       = "manga-cdn-http-forwarding-rule"
  project    = var.project_id
  target     = google_compute_target_http_proxy.cdn_http_proxy.id
  port_range = "80"
  ip_address = google_compute_global_address.cdn_ip.address

  depends_on = [google_project_service.compute]
}

# URL Map for HTTP to HTTPS redirect
resource "google_compute_url_map" "https_redirect" {
  name    = "manga-https-redirect"
  project = var.project_id

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }

  depends_on = [google_project_service.compute]
}

# Update HTTP proxy to use redirect URL map
resource "google_compute_target_http_proxy" "cdn_http_redirect_proxy" {
  name    = "manga-cdn-http-redirect-proxy"
  project = var.project_id
  url_map = google_compute_url_map.https_redirect.id

  depends_on = [google_project_service.compute]
}

# DNS Record (if custom domain provided)
resource "google_dns_record_set" "cdn_dns" {
  count = var.custom_domain != "" && var.dns_zone_name != "" ? 1 : 0
  
  name         = "${var.custom_domain}."
  type         = "A"
  ttl          = 300
  managed_zone = var.dns_zone_name
  project      = var.project_id

  rrdatas = [google_compute_global_address.cdn_ip.address]

  depends_on = [google_project_service.compute]
}

# Cloud Armor Security Policy (DDoS Protection)
resource "google_compute_security_policy" "cdn_security_policy" {
  name    = "manga-cdn-security-policy"
  project = var.project_id

  description = "Security policy for manga CDN"

  # Allow Japan and major regions
  rule {
    action   = "allow"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = [
          "0.0.0.0/0"  # Allow all for hackathon demo
        ]
      }
    }
    description = "Allow all traffic for demo"
  }

  # Rate limiting rule
  rule {
    action   = "throttle"
    priority = "2000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
    }
    description = "Rate limit: 100 req/min per IP"
  }

  # Default rule
  rule {
    action   = "deny(403)"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default deny"
  }

  depends_on = [google_project_service.compute]
}

