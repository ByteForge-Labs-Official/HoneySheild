"""Fine-grained events feed."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.models.attack import Event
from app.schemas.attacks import EventOut

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/{attack_id}", response_model=list[EventOut])
async def attack_events(
    attack_id: UUID, _: CurrentUser, db: DBSession,
    limit: int = Query(100, le=1000),
):
    res = await db.execute(
        select(Event).where(Event.attack_id == attack_id)
        .order_by(Event.ts.asc()).limit(limit)
    )
    return res.scalars().all()