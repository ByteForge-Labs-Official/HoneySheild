"""Authentication / authorization dependencies."""
from __future__ import annotations

from typing import Iterable

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import AuthError, ForbiddenError
from app.core.security import decode_token
from app.db.repositories.user_repository import UserRepository
from app.db.session import DbSession

_bearer = HTTPBearer(auto_error=False, description="JWT access token")


async def get_current_user(
    session: DbSession,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if creds is None or not creds.credentials:
        raise AuthError("Missing bearer token")
    try:
        payload = decode_token(creds.credentials)
    except Exception as e:  # noqa: BLE001
        raise AuthError("Invalid or expired token") from e
    if payload.type != "access":
        raise AuthError("Wrong token type")
    repo = UserRepository(session)
    user = await repo.get_by_id(payload.sub)
    if user is None or not user.get("is_active", False):
        raise AuthError("User no longer active")
    user["_token_roles"] = list(payload.roles)
    return user


def require_roles(*roles: str):
    """Dependency factory that enforces role-based access on a route."""
    needed: set[str] = set(roles)

    async def _checker(user: dict = Depends(get_current_user)) -> dict:
        user_roles = set(user.get("_token_roles") or user.get("roles") or [])
        if not (user_roles & needed):
            raise ForbiddenError("Insufficient role")
        return user

    return _checker