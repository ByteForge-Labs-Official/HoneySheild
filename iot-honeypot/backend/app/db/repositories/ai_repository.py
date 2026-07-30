"""AI-insight repository."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, select

from app.db.models.ai import AIInsight


class AIInsightRepository:
    def __init__(self, session) -> None:
        self.session = session

    async def create(self, *, model, summary, mitre_attack=None, confidence=0.0, data=None) -> dict:
        ins = AIInsight(
            model=model,
            summary=summary,
            mitre_attack=mitre_attack or [],
            confidence=confidence,
            data=data or {},
        )
        self.session.add(ins)
        await self.session.flush()
        await self.session.refresh(ins)
        return _to_dict(ins)

    async def list_for_event(self, event_id: str | uuid.UUID, *, limit: int = 5) -> list[dict]:
        stmt = (
            select(AIInsight)
            .where(AIInsight.honeypot_event_id == uuid.UUID(str(event_id)))
            .order_by(desc(AIInsight.created_at))
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return [_to_dict(r) for r in rows]


def _to_dict(i: AIInsight) -> dict:
    return {
        "id": str(i.id),
        "honeypot_event_id": str(i.honeypot_event_id) if i.honeypot_event_id else None,
        "model": i.model,
        "summary": i.summary,
        "mitre_attack": list(i.mitre_attack or []),
        "confidence": i.confidence,
        "data": i.data,
        "created_at": i.created_at,
    }