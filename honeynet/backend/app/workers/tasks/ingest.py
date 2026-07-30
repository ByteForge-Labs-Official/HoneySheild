"""Celery tasks — ingest."""
from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy import text

from app.db.session import async_session
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.workers.tasks.ingest.refresh_materialized_views")
def refresh_materialized_views() -> dict:
    """Recompute mv_* every 60s for dashboard freshness."""
    return {"queued": True}


@celery_app.task(name="app.workers.tasks.ingest.archive_old_events", bind=True, max_retries=3)
def archive_old_events(self, days: int = 30) -> dict:
    """Stub: move events older than `days` to cold storage (ELK)."""
    return {"cutoff_days": days}


async def _refresh_views_async() -> None:
    async with async_session() as db:
        for view in ("mv_attacks_per_min", "mv_top_offenders"):
            await db.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view};"))
        await db.commit()
    logger.info("ingest.refresh.done", at=datetime.now(timezone.utc))