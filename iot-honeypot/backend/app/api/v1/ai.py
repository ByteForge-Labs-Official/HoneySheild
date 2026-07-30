"""AI insight routes."""
from __future__ import annotations

from fastapi import APIRouter

from app.apideps.auth import require_roles
from app.db.repositories.ai_repository import AIInsightRepository
from app.db.session import DbSession

router = APIRouter()


@router.get(
    "/events/{event_id}/insights",
    summary="List AI insights for an event",
)
async def insights_for_event(
    event_id: str, session: DbSession, _: dict = require_roles("analyst", "admin")
) -> list[dict]:
    return await AIInsightRepository(session).list_for_event(event_id)