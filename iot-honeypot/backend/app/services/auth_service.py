"""Auth service (login, refresh, registration)."""
from __future__ import annotations

from fastapi import status

from app.core.config import get_settings
from app.core.errors import AuthError, ConflictError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.repositories.user_repository import UserRepository
from app.schemas.auth import TokenOut


class AuthService:
    def __init__(self, session) -> None:
        self.session = session
        self.repo = UserRepository(session)
        self.s = get_settings()

    async def login(self, *, username: str, password: str) -> TokenOut:
        user = await self.repo.get_by_username(username)
        if user is None:
            user = await self.repo.get_by_email(username)
        if user is None or not verify_password(password, user["hashed_password"]):
            raise AuthError("Invalid credentials")
        if not user["is_active"]:
            raise AuthError("User disabled")
        await self.repo.touch_login(user["id"])
        await self.session.commit()
        return self._tokens(user)

    async def refresh(self, *, refresh_token: str) -> TokenOut:
        try:
            payload = decode_token(refresh_token)
        except Exception as e:  # noqa: BLE001
            raise AuthError("Invalid refresh token") from e
        if payload.type != "refresh":
            raise AuthError("Wrong token type")
        user = await self.repo.get_by_id(payload.sub)
        if user is None or not user["is_active"]:
            raise AuthError("User no longer active")
        return self._tokens(user)

    async def register(
        self, *, email: str, username: str, password: str, full_name: str | None
    ) -> TokenOut:
        if await self.repo.get_by_email(email):
            raise ConflictError("Email already registered")
        if await self.repo.get_by_username(username):
            raise ConflictError("Username taken")
        user = await self.repo.create(
            email=email,
            username=username,
            password=password,
            full_name=full_name,
            roles=["analyst"],
        )
        await self.session.commit()
        return self._tokens(user)

    def _tokens(self, user: dict) -> TokenOut:
        return TokenOut(
            access_token=create_access_token(
                subject=user["id"], roles=user.get("roles", [])
            ),
            refresh_token=create_refresh_token(subject=user["id"]),
            expires_in=self.s.jwt_access_ttl_min * 60,
        )