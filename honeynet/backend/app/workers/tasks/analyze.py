"""Celery tasks — AI analysis."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog

from app.db.session import async_session
from app.integrations.ai.provider import get_provider
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.workers.tasks.analyze.summarize_recent",
                 bind=True, max_retries=2, default_retry_delay=30)
def summarize_recent(self, window_minutes: int = 15) -> dict:
    """Pull the last `window_minutes` worth of attacks, ask the AI provider for
    a summary and MITRE tags, and persist them."""
    return _as_sync(_summarize(window_minutes))


async def _summarize(window_minutes: int) -> dict:
    from sqlalchemy import select
    from app.models.attack import Attack
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    async with async_session() as db:
        rows = (await db.execute(
            select(Attack).where(Attack.started_at >= cutoff).limit(500)
        )).scalars().all()
    if not rows:
        return {"rows": 0}

    events = [{"protocol": r.protocol, "src_ip": r.src_ip, "payload": r.payload,
               "severity": r.severity} for r in rows]

    provider = get_provider()
    summary = await provider.summarise(events)
    tags    = await provider.tag_mitre(events)
    iocs    = await provider.extract_iocs(events)

    logger.info("analyze.summary.done", rows=len(rows), tags=len(tags), iocs=len(iocs))
    return {"rows": len(rows), "summary": summary, "tags": tags, "iocs": iocs}


def _as_sync(coro):
    import asyncio
    return asyncio.run(coro)