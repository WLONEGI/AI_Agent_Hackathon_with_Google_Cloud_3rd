# Outputs for Storage Module

output "bucket_names" {
  description = "Map of bucket purposes to their names"
  value = {
    input_data        = google_storage_bucket.manga_input_data.name
    output_images     = google_storage_bucket.manga_output_images.name
    preview_cache     = google_storage_bucket.manga_preview_cache.name
    version_snapshots = google_storage_bucket.manga_version_snapshots.name
    final_products    = google_storage_bucket.manga_final_products.name
    temp_data         = google_storage_bucket.manga_temp_data.name
  }
}

output "bucket_urls" {
  description = "Map of bucket purposes to their URLs"
  value = {
    input_data        = google_storage_bucket.manga_input_data.url
    output_images     = google_storage_bucket.manga_output_images.url
    preview_cache     = google_storage_bucket.manga_preview_cache.url
    version_snapshots = google_storage_bucket.manga_version_snapshots.url
    final_products    = google_storage_bucket.manga_final_products.url
    temp_data         = google_storage_bucket.manga_temp_data.url
  }
}

output "public_preview_url" {
  description = "Public URL for preview cache bucket (if public access enabled)"
  value       = var.enable_public_preview_access ? "https://storage.googleapis.com/${google_storage_bucket.manga_preview_cache.name}" : null
}