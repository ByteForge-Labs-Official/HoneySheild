#!/usr/bin/env bash
# Seed the first admin user from environment.
# ADMIN_EMAIL ADMIN_USERNAME ADMIN_PASSWORD ADMIN_FULL_NAME
set -euo pipefail
cd "$(dirname "$0")/.."
exec python -m app.scripts.seed_admin \
  --email "${ADMIN_EMAIL:-admin@honeynet.local}" \
  --username "${ADMIN_USERNAME:-admin}" \
  --password "${ADMIN_PASSWORD:-changeme-changeme}" \
  --full-name "${ADMIN_FULL_NAME:-Honeynet Admin}"