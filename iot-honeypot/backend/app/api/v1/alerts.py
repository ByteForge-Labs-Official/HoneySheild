"""Alert read routes (queries persisted alerts)."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.apideps.auth import require_roles
from app.db.repositories.alert_repository import AlertRepository
from app.db.session import DbSession
from app.schemas.alert import AlertOut

router = APIRouter()


@router.get("", response_model=list[AlertOut], summary="List recent alerts")
async def list_alerts(
    limit: int = Query(default=100, ge=1, le=1000),
    severity_min: int | None = Query(default=None, ge=1, le=4),
    session: DbSession = None,
    _: dict = require_roles("analyst", "admin"),
) -> list[AlertOut]:
    rows = await AlertRepository(session).list_recent(limit=limit, severity_min=severity_min)
    return [AlertOut(**r) for r in rows]