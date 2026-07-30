#!/usr/bin/env bash
# Start the API in development with hot reload.
set -euo pipefail
cd "$(dirname "$0")/.."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info