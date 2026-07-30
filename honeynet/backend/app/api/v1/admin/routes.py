"""Admin endpoints — tokens, audit log."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import AdminUser, DBSession
from app.models.audit import AuditLog
from datetime import datetime, timezone

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit", response_model=list[dict])
async def _audit(_: AdminUser, db: DBSession, limit: int = 200):
    res = await db.execute(select(AuditLog).order_by(AuditLog.ts.desc()).limit(limit))
    return [{"id": str(r.id), "actor_id": str(r.actor_id) if r.actor_id else None,
             "action": r.action, "target": r.target, "ip": r.ip, "ts": r.ts,
             "metadata": r.metadata_json} for r in res.scalars().all()]


@router.post("/users/disable/{user_id}")
async def _disable(user_id: UUID, _: AdminUser, db: DBSession):
    from app.models.user import User
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Not found")
    u.is_active = False
    db.add(AuditLog(action="user.disable", target=str(user_id), ts=datetime.now(timezone.utc),
                    actor_id=_.id, ip="api"))
    await db.commit()
    return {"disabled": str(user_id)}