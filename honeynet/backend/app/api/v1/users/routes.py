"""User management — admin-only CRUD."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import AdminUser, DBSession
from app.core.security.hashing import hash_password
from app.models.user import User
from app.schemas.auth import UserOut
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
async def list_users(_: AdminUser, db: DBSession):
    res = await db.execute(select(User).order_by(User.created_at.desc()))
    return res.scalars().all()


@router.post("/", response_model=UserOut, status_code=201)
async def create_user(body: dict, _: AdminUser, db: DBSession):
    if (await db.execute(select(User).where(User.email == body["email"]))).scalar_one_or_none():
        raise HTTPException(409, "Email already exists")
    user = User(
        email=body["email"].lower().strip(),
        username=body["username"],
        password_hash=hash_password(body["password"]),
        is_admin=bool(body.get("is_admin", False)),
        is_active=True,
    )
    db.add(user); await db.commit(); await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: UUID, _: AdminUser, db: DBSession):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Not found")
    await db.delete(user); await db.commit()