#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
. .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8080 >/tmp/uvicorn.log 2>&1 & echo $!
