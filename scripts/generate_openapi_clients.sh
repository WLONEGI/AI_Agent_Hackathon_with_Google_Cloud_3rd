#!/usr/bin/env bash
set -euo pipefail

GENERATOR_IMAGE="${GENERATOR_IMAGE:-openapitools/openapi-generator-cli:v7.8.0}"
SPEC_PATH="${SPEC_PATH:-docs/05.API_openapi.yaml}"
OUTPUT_BASE="${OUTPUT_BASE:-clients}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker command not found. Install Docker or use the GitHub Actions workflow." >&2
  exit 1
fi

echo "Generating SDKs from ${SPEC_PATH} using ${GENERATOR_IMAGE}" >&2

mkdir -p "${OUTPUT_BASE}"

docker run --rm -v "$(pwd)":/local "${GENERATOR_IMAGE}" generate \
  -i "/local/${SPEC_PATH}" \
  -g typescript-fetch \
  -o "/local/${OUTPUT_BASE}/typescript-fetch"

docker run --rm -v "$(pwd)":/local "${GENERATOR_IMAGE}" generate \
  -i "/local/${SPEC_PATH}" \
  -g python \
  -o "/local/${OUTPUT_BASE}/python"

echo "SDKs generated under ${OUTPUT_BASE}/" >&2
