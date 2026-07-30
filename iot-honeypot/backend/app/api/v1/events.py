"""Honeypot event ingest + read routes."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query

from app.api.deps.auth import require_roles
from app.db.session import DbSession
from app.schemas.honeypot import HoneypotEventOut
from app.services.honeypot_service import HoneypotService

router = APIRouter()


@router.get(
    "/recent",
    response_model=list[HoneypotEventOut],
    summary="List most recent events (across all honeypots)",
)
async def recent_events(
    session: DbSession,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[HoneypotEventOut]:
    """Public feed of recent honeypot events for the live telemetry dashboard."""
    rows = await HoneypotService(session).recent_events(None, limit=limit)
    return [HoneypotEventOut(**r) for r in rows]


@router.post(
    "/{honeypot_id}",
    response_model=HoneypotEventOut,
    status_code=201,
    summary="Ingest a honeypot event",
)
@router.post(
    "/{honeypot_id}/events",
    response_model=HoneypotEventOut,
    status_code=201,
    summary="Ingest a honeypot event (legacy alias)",
)
async def ingest(
    honeypot_id: str,
    session: DbSession,
    body: dict = Body(...),
) -> HoneypotEventOut:
    """Used by honeypot bridges to push raw events into the API. No auth required."""
    event_type = body.pop("event_type", "unknown")
    protocol   = body.pop("protocol", "ssh")
    src_ip     = body.pop("src_ip", None)
    src_port   = body.pop("src_port", None)
    dst_port   = body.pop("dst_port", None)
    session_id = body.pop("session_id", None)
    raw_size   = body.pop("raw_size", 0)
    payload    = body.pop("payload", body) or {}

    ev = await HoneypotService(session).ingest_event(honeypot_id, {
        "event_type": event_type,
        "protocol":   protocol,
        "src_ip":     src_ip,
        "src_port":   src_port,
        "dst_port":   dst_port,
        "session_id": session_id,
        "raw_size":   raw_size,
        "payload":    payload,
    })
    return HoneypotEventOut(**ev)


@router.get(
    "/{honeypot_id}",
    response_model=list[HoneypotEventOut],
    summary="List recent events for a specific honeypot",
)
async def list_events(
    honeypot_id: str,
    session: DbSession,
    limit: int = Query(default=100, ge=1, le=1000),
    user_roles: dict = Depends(require_roles("analyst", "admin")),
) -> list[HoneypotEventOut]:
    rows = await HoneypotService(session).recent_events(honeypot_id, limit=limit)
    return [HoneypotEventOut(**r) for r in rows]