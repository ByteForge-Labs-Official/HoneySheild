"""Reusable dependencies."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.jwt import decode_token
from app.db.session import get_db
from app.integrations.redis.client import get_redis
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing token")
    payload = decode_token(token, expected_type="access")
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="user inactive")
    return user


async def get_admin_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="admin required")
    return user


async def get_redis_dep():
    return await get_redis()


DBSession = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[object, Depends(get_redis_dep)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
