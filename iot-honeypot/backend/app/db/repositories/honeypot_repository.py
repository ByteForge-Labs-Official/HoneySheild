"""Honeypot + HoneypotEvent repositories."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, func, select

from app.db.models.honeypot import Honeypot, HoneypotEvent


class HoneypotRepository:
    def __init__(self, session) -> None:
        self.session = session

    async def list(self, *, enabled: bool | None = None) -> list[dict]:
        stmt = select(Honeypot).order_by(Honeypot.name)
        if enabled is not None:
            stmt = stmt.where(Honeypot.enabled == enabled)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [_honeypot_to_dict(r) for r in rows]

    async def get(self, honeypot_id: str | uuid.UUID) -> dict | None:
        row = await self.session.get(Honeypot, uuid.UUID(str(honeypot_id)))
        return _honeypot_to_dict(row) if row else None

    async def create(self, *, name, kind, host, port, vendor=None, enabled=True, config=None) -> dict:
        hp = Honeypot(
            name=name,
            kind=kind,
            vendor=vendor,
            host=host,
            port=port,
            enabled=enabled,
            config=config or {},
        )
        self.session.add(hp)
        await self.session.flush()
        await self.session.refresh(hp)
        return _honeypot_to_dict(hp)

    async def update(self, honeypot_id: str | uuid.UUID, **patch: Any) -> dict:
        hp = await self.session.get(Honeypot, uuid.UUID(str(honeypot_id)))
        if hp is None:
            return None
        for k, v in patch.items():
            setattr(hp, k, v)
        await self.session.flush()
        await self.session.refresh(hp)
        return _honeypot_to_dict(hp)

    async def delete(self, honeypot_id: str | uuid.UUID) -> bool:
        hp = await self.session.get(Honeypot, uuid.UUID(str(honeypot_id)))
        if hp is None:
            return False
        await self.session.delete(hp)
        await self.session.flush()
        return True


class HoneypotEventRepository:
    def __init__(self, session) -> None:
        self.session = session

    async def create(self, *, honeypot_id, event_type, protocol, payload, **kw) -> dict:
        ev = HoneypotEvent(
            honeypot_id=uuid.UUID(str(honeypot_id)),
            event_type=event_type,
            protocol=protocol,
            payload=payload or {},
            **kw,
        )
        self.session.add(ev)
        await self.session.flush()
        await self.session.refresh(ev)
        return _event_to_dict(ev)

    async def list_recent(self, *, honeypot_id=None, limit: int = 100) -> list[dict]:
        stmt = select(HoneypotEvent).order_by(desc(HoneypotEvent.created_at)).limit(limit)
        if honeypot_id:
            stmt = stmt.where(HoneypotEvent.honeypot_id == uuid.UUID(str(honeypot_id)))
        rows = (await self.session.execute(stmt)).scalars().all()
        return [_event_to_dict(r) for r in rows]

    async def count_by_protocol(self, *, since=None) -> dict[str, int]:
        stmt = select(HoneypotEvent.protocol, func.count()).group_by(HoneypotEvent.protocol)
        if since is not None:
            stmt = stmt.where(HoneypotEvent.created_at >= since)
        rows = (await self.session.execute(stmt)).all()
        return {proto: int(count) for proto, count in rows}


def _honeypot_to_dict(h: Honeypot) -> dict:
    return {
        "id": str(h.id),
        "name": h.name,
        "kind": h.kind,
        "vendor": h.vendor,
        "host": h.host,
        "port": h.port,
        "enabled": h.enabled,
        "config": h.config or {},
        "created_at": h.created_at,
        "updated_at": h.updated_at,
    }


def _event_to_dict(e: HoneypotEvent) -> dict:
    return {
        "id": str(e.id),
        "honeypot_id": str(e.honeypot_id),
        "event_type": e.event_type,
        "protocol": e.protocol,
        "src_ip": str(e.src_ip) if e.src_ip is not None else None,
        "src_port": e.src_port,
        "dst_port": e.dst_port,
        "session_id": e.session_id,
        "payload": e.payload or {},
        "raw_size": e.raw_size or 0,
        "created_at": e.created_at,
    }