"""Attack query/read API."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBSession
from app.models.attack import Attack
from app.schemas.attacks import AttackDetail, AttackOut, AttackPage, AttackQuery

router = APIRouter(prefix="/attacks", tags=["attacks"])


@router.get("/", response_model=AttackPage)
async def list_attacks(
    _: CurrentUser, db: DBSession,
    q: AttackQuery = Query(),                       # noqa: B008
):
    stmt = select(Attack)
    if q.protocol:  stmt = stmt.where(Attack.protocol == q.protocol)
    if q.severity:  stmt = stmt.where(Attack.severity == q.severity)
    if q.src_ip:    stmt = stmt.where(Attack.src_ip == q.src_ip)
    if q.since:     stmt = stmt.where(Attack.started_at >= q.since)
    if q.until:     stmt = stmt.where(Attack.started_at <= q.until)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (await db.execute(
        stmt.order_by(Attack.started_at.desc()).offset(q.offset).limit(q.limit)
    )).scalars().all()
    return AttackPage(total=total or 0, items=[AttackOut.model_validate(r) for r in rows])


@router.get("/{attack_id}", response_model=AttackDetail)
async def get_attack(attack_id: UUID, _: CurrentUser, db: DBSession):
    a = await db.get(Attack, attack_id)
    if not a:
        raise HTTPException(404, "Not found")
    return a


@router.get("/recent/24h", response_model=list[AttackOut])
async def last_24h(_: CurrentUser, db: DBSession):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    res = await db.execute(
        select(Attack).where(Attack.started_at >= cutoff).order_by(Attack.started_at.desc()).limit(200)
    )
    return res.scalars().all()