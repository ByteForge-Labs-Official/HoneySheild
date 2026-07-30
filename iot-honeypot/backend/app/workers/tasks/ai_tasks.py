"""AI enrichment Celery tasks."""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.logging import get_logger
from app.db.repositories.ai_repository import AIInsightRepository
from app.db.session import SessionMaker
from app.db.models.honeypot import HoneypotEvent
from app.integrations.ai.nlp import summarise_event
from app.workers.celery_app import celery_app

log = get_logger(__name__)


@celery_app.task(name="app.workers.tasks.ai_tasks.enrich_pending_events")
def enrich_pending_events(limit: int = 50) -> int:
    """Find the N most recent events lacking insights, run AI, persist."""
    return asyncio.run(_enrich(limit))


async def _enrich(limit: int) -> int:
    enriched = 0
    async with SessionMaker() as session:
        stmt = select(HoneypotEvent).order_by(HoneypotEvent.created_at.desc()).limit(limit)
        events = (await session.execute(stmt)).scalars().all()
        repo = AIInsightRepository(session)
        for ev in events:
            try:
                summary = await summarise_event({
                    "event_type": ev.event_type,
                    "protocol": ev.protocol,
                    "src_ip": ev.src_ip,
                    "payload": ev.payload,
                })
                repo_create = await repo.create(
                    model="local-llm",
                    summary=summary["summary"],
                    mitre_attack=summary.get("mitre", []),
                    confidence=summary.get("confidence", 0.0),
                    data=summary,
                )
                ev._ai_insight_id = repo_create["id"]
                enriched += 1
            except Exception as e:  # noqa: BLE001
                log.warning("ai.enrich_failed", error=str(e))
        await session.commit()
    return enriched