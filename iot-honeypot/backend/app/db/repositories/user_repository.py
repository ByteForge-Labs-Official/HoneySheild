"""User repository."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update

from app.db.models.user import User
from app.core.security import hash_password


class UserRepository:
    def __init__(self, session) -> None:
        self.session = session

    async def get_by_id(self, user_id: str | uuid.UUID) -> dict | None:
        row = await self.session.get(User, uuid.UUID(str(user_id)))
        return _to_dict(row) if row else None

    async def get_by_email(self, email: str) -> dict | None:
        stmt = select(User).where(User.email == email.lower())
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        return _to_dict(row) if row else None

    async def get_by_username(self, username: str) -> dict | None:
        stmt = select(User).where(User.username == username)
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        return _to_dict(row) if row else None

    async def create(
        self,
        *,
        email: str,
        username: str,
        password: str,
        full_name: str | None = None,
        roles: list[str] | None = None,
        is_superuser: bool = False,
    ) -> dict:
        user = User(
            email=email.lower(),
            username=username,
            full_name=full_name,
            hashed_password=hash_password(password),
            roles=roles or ["analyst"],
            is_superuser=is_superuser,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return _to_dict(user)

    async def touch_login(self, user_id: uuid.UUID) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(last_login_at=datetime.utcnow())
        )


def _to_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "hashed_password": user.hashed_password,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "roles": list(user.roles or []),
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login_at": user.last_login_at,
    }