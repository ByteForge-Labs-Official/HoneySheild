"""Honeypot event ingest + read routes."""
from __future__ import annotations

from fastapi import APIRouter, Body, Query

from app.apideps.auth import get_current_user, require_roles
from app.db.session import DbSession
from app.schemas.honeypot import HoneypotEventOut
from app.services.honeypot_service import HoneypotService

router = APIRouter()


@router.post(
    "/{honeypot_id}/events",
    response_model=HoneypotEventOut,
    status_code=201,
    summary="Ingest a honeypot event",
)
async def ingest(
    honeypot_id: str,
    payload: dict = Body(...),
    session: DbSession = None,
) -> HoneypotEventOut:
    """Used by honeypot bridges to push raw events into the API."""
    ev = await HoneypotService(session).ingest_event(honeypot_id, payload)
    return HoneypotEventOut(**ev)


@router.get(
    "/{honeypot_id}/events",
    response_model=list[HoneypotEventOut],
    summary="List recent events",
)
async def list_events(
    honeypot_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    session: DbSession = None,
    _: dict = require_roles("analyst", "admin"),
) -> list[HoneypotEventOut]:
    rows = await HoneypotService(session).recent_events(honeypot_id, limit=limit)
    return [HoneypotEventOut(**r) for r in rows]


@router.get(
    "/events/recent",
    response_model=list[HoneypotEventOut],
    summary="List most recent events (across all honeypots)",
)
async def recent_events(
    limit: int = Query(default=100, ge=1, le=1000),
    session: DbSession = None,
    _: dict = require_roles("analyst", "admin"),
) -> list[HoneypotEventOut]:
    rows = await HoneypotService(session).recent_events(None, limit=limit)
    return [HoneypotEventOut(**r) for r in rows]