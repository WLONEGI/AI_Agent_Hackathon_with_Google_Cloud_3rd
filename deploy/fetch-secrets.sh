#!/usr/bin/env bash
set -euo pipefail

# Usage: PROJECT_ID=my-project ./deploy/fetch-secrets.sh .env.gcp

OUTPUT_FILE=${1:-.env.gcp}
PROJECT_ID=${PROJECT_ID:?"PROJECT_ID environment variable is required"}
SECRET_PREFIX=${SECRET_PREFIX:-spell-backend}

SECRETS=(
  AUTH_SECRET_KEY
  DATABASE_URL
  FIREBASE_PRIVATE_KEY
  CLOUD_TASKS_SERVICE_URL
  VERTEX_CREDENTIALS_JSON
)

echo "# Generated $(date -u +"%Y-%m-%dT%H:%M:%SZ")" > "${OUTPUT_FILE}"
echo "# Source: Google Secret Manager (${PROJECT_ID})" >> "${OUTPUT_FILE}"

for name in "${SECRETS[@]}"; do
  secret_id="${SECRET_PREFIX}_${name}"
  if gcloud secrets describe "${secret_id}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    echo "Fetching ${secret_id}" >&2
    value=$(gcloud secrets versions access latest --project "${PROJECT_ID}" --secret "${secret_id}")
    printf '%s=%s\n' "${name}" "${value}" >> "${OUTPUT_FILE}"
  else
    echo "Skipping missing secret ${secret_id}" >&2
    printf '# %s not found in %s\n' "${secret_id}" "${PROJECT_ID}" >> "${OUTPUT_FILE}"
  fi
done

echo "Secrets written to ${OUTPUT_FILE}" >&2
