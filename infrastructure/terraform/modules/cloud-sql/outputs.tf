# Outputs for Cloud SQL Module

output "instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = google_sql_database_instance.manga_db.name
}

output "instance_connection_name" {
  description = "Connection name for the Cloud SQL instance"
  value       = google_sql_database_instance.manga_db.connection_name
}

output "private_ip_address" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.manga_db.private_ip_address
}

output "database_name" {
  description = "Name of the created database"
  value       = google_sql_database.manga_database.name
}

output "database_username" {
  description = "Database username"
  value       = google_sql_user.manga_user.name
}

output "database_password_secret" {
  description = "Secret Manager secret name containing the database password"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "ssl_cert" {
  description = "SSL certificate details"
  value = {
    common_name = google_sql_ssl_cert.client_cert.common_name
    cert        = google_sql_ssl_cert.client_cert.cert
    private_key = google_sql_ssl_cert.client_cert.private_key
  }
  sensitive = true
}

output "database_url" {
  description = "Database connection URL for applications"
  value       = "postgresql+asyncpg://${google_sql_user.manga_user.name}:${random_password.db_password.result}@${google_sql_database_instance.manga_db.private_ip_address}:5432/${google_sql_database.manga_database.name}"
  sensitive   = true
}

output "readonly_username" {
  description = "Read-only database username"
  value       = google_sql_user.readonly_user.name
}