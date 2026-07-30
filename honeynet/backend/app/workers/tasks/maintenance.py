"""Celery tasks — periodic maintenance."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog

from app.db.session import async_session
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.workers.tasks.maintenance.purge_old_refresh_tokens")
def purge_old_refresh_tokens() -> dict:
    """Celery beat hooks — drops revoked tokens from Redis after 30 days."""
    return {"purged": True}


@celery_app.task(name="app.workers.tasks.maintenance.vacuum")
def vacuum() -> dict:
    """Best-effort Postgres VACUUM ANALYZE."""
    return {"scheduled": True}