"""Threat intelligence — IOC CRUD + MITRE feedback."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DBSession
from app.models.ioc import IOC
from app.schemas.analytics import IOCOut, ThreatFeedback

router = APIRouter(prefix="/threats", tags=["threats"])


@router.get("/iocs", response_model=list[IOCOut])
async def _list(_: CurrentUser, db: DBSession, kind: str | None = None, limit: int = 100):
    stmt = select(IOC).order_by(IOC.last_seen.desc()).limit(limit)
    if kind:
        stmt = stmt.where(IOC.kind == kind)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/iocs", response_model=IOCOut, status_code=201)
async def _upsert(body: dict, _: AdminUser, db: DBSession):
    existing = (await db.execute(
        select(IOC).where(IOC.value == body["value"], IOC.kind == body["kind"])
    )).scalar_one_or_none()
    if existing:
        existing.last_seen = datetime.now(timezone.utc)
        existing.confidence = max(existing.confidence, body.get("confidence", 0))
        existing.tags = list(set(existing.tags + body.get("tags", [])))
        await db.commit()
        return existing
    ioc = IOC(
        value=body["value"], kind=body["kind"],
        first_seen=datetime.now(timezone.utc), last_seen=datetime.now(timezone.utc),
        confidence=body.get("confidence", 0),
        source=body.get("source", "manual"),
        tags=body.get("tags", []),
    )
    db.add(ioc); await db.commit(); await db.refresh(ioc)
    return ioc


@router.post("/feedback", status_code=204)
async def _feedback(body: ThreatFeedback, _: CurrentUser, db: DBSession):
    if not await db.get(IOC, body.ioc_id):
        raise HTTPException(404, "IOC not found")
    # Stub — persist feedback into a separate table in the next migration.
    return None