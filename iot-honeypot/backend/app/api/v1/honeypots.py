"""Honeypot CRUD routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import require_roles
from app.db.session import DbSession
from app.schemas.honeypot import HoneypotCreate, HoneypotOut, HoneypotUpdate
from app.services.honeypot_service import HoneypotService

router = APIRouter()


@router.get("", response_model=list[HoneypotOut], summary="List honeypots")
async def list_honeypots(
    session: DbSession,
    enabled: bool | None = Query(default=None),
    user_roles: dict = Depends(require_roles("analyst", "admin")),
) -> list[HoneypotOut]:
    items = await HoneypotService(session).list(enabled=enabled)
    return [HoneypotOut(**i) for i in items]


@router.post("", response_model=HoneypotOut, status_code=201, summary="Create honeypot")
async def create_honeypot(
    payload: HoneypotCreate, session: DbSession, user_roles: dict = Depends(require_roles("admin"))
) -> HoneypotOut:
    hp = await HoneypotService(session).create(payload.model_dump())
    return HoneypotOut(**hp)


@router.patch("/{honeypot_id}", response_model=HoneypotOut, summary="Update honeypot")
async def update_honeypot(
    honeypot_id: str,
    patch: HoneypotUpdate,
    session: DbSession,
    user_roles: dict = Depends(require_roles("admin")),
) -> HoneypotOut:
    hp = await HoneypotService(session).update(honeypot_id, patch.model_dump(exclude_unset=True))
    return HoneypotOut(**hp)


@router.delete("/{honeypot_id}", status_code=204, summary="Delete honeypot")
async def delete_honeypot(
    honeypot_id: str, session: DbSession, user_roles: dict = Depends(require_roles("admin"))
) -> None:
    await HoneypotService(session).delete(honeypot_id)