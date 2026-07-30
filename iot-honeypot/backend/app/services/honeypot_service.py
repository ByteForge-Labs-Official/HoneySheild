"""Honeypot service: CRUD, ingest, analytics."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.errors import ConflictError, NotFoundError
from app.db.repositories.honeypot_repository import HoneypotEventRepository, HoneypotRepository


class HoneypotService:
    def __init__(self, session) -> None:
        self.session = session
        self.repo = HoneypotRepository(session)
        self.events = HoneypotEventRepository(session)

    async def list(self, *, enabled: bool | None = None) -> list[dict]:
        return await self.repo.list(enabled=enabled)

    async def create(self, payload: dict) -> dict:
        existing = [h for h in await self.repo.list() if h["name"] == payload["name"]]
        if existing:
            raise ConflictError("Honeypot name already exists")
        hp = await self.repo.create(**payload)
        await self.session.commit()
        return hp

    async def update(self, honeypot_id: str, patch: dict) -> dict:
        hp = await self.repo.update(honeypot_id, **{k: v for k, v in patch.items() if v is not None})
        if hp is None:
            raise NotFoundError("Honeypot not found")
        await self.session.commit()
        return hp

    async def delete(self, honeypot_id: str) -> None:
        ok = await self.repo.delete(honeypot_id)
        if not ok:
            raise NotFoundError("Honeypot not found")
        await self.session.commit()

    async def ingest_event(self, honeypot_id: str, payload: dict) -> dict:
        ev = await self.events.create(honeypot_id=honeypot_id, **payload)
        await self.session.commit()
        return ev

    async def recent_events(self, honeypot_id: str | None = None, *, limit: int = 100) -> list[dict]:
        return await self.events.list_recent(honeypot_id=honeypot_id, limit=limit)

    async def protocol_breakdown(self, *, window_minutes: int = 60) -> dict[str, int]:
        since = datetime.now(tz=timezone.utc) - timedelta(minutes=window_minutes)
        return await self.events.count_by_protocol(since=since)