#!/usr/bin/env bash
# Entrypoint switches between API / worker / beat / flower per first arg.
set -Eeuo pipefail

cmd="${1:-api}"
shift || true

case "$cmd" in
  api)
    exec uvicorn app.main:app \
      --host "${BACKEND_HOST:-0.0.0.0}" \
      --port "${BACKEND_PORT:-8000}" \
      --workers "${BACKEND_WORKERS:-2}" \
      --proxy-headers --forwarded-allow-ips='*' \
      --no-server-header \
      --access-log
    ;;
  worker)
    exec celery -A app.workers.celery_app worker \
      --loglevel="${LOG_LEVEL:-INFO}" \
      --concurrency="${CELERY_CONCURRENCY:-4}" \
      -Q default,ingest,analyze
    ;;
  beat)
    exec celery -A app.workers.celery_app beat \
      --loglevel="${LOG_LEVEL:-INFO}"
    ;;
  flower)
    exec celery -A app.workers.celery_app flower \
      --port="${FLOWER_PORT:-5555}"
    ;;
  bootstrap)
    exec python -m app.core.cli bootstrap
    ;;
  shell)
    exec python -m IPython
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    exit 2
    ;;
esac
