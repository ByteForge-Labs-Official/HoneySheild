#!/usr/bin/env bash
# Run Alembic migrations (upgrade head).
set -euo pipefail
cd "$(dirname "$0")/.."
exec alembic upgrade head