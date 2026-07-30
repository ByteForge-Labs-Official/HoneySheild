"""Alert repository."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, select

from app.db.models.ids import Alert


class AlertRepository:
    def __init__(self, session) -> None:
        self.session = session

    async def create(self, *, source, signature, category, severity, **kw) -> dict:
        a = Alert(source=source, signature=signature, category=category, severity=severity, **kw)
        self.session.add(a)
        await self.session.flush()
        await self.session.refresh(a)
        return _alert_to_dict(a)

    async def list_recent(self, *, limit: int = 100, severity_min: int | None = None) -> list[dict]:
        stmt = select(Alert).order_by(desc(Alert.created_at)).limit(limit)
        if severity_min is not None:
            stmt = stmt.where(Alert.severity >= severity_min)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [_alert_to_dict(r) for r in rows]


def _alert_to_dict(a: Alert) -> dict:
    return {
        "id": str(a.id),
        "source": a.source,
        "signature": a.signature,
        "category": a.category,
        "severity": a.severity,
        "src_ip": a.src_ip,
        "dst_ip": a.dst_ip,
        "confidence": a.confidence,
        "raw": a.raw,
        "honeypot_event_id": str(a.honeypot_event_id) if a.honeypot_event_id else None,
        "created_at": a.created_at,
    }