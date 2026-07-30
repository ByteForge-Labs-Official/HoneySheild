"""Authentication — login, refresh, logout."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.core.security.jwt import decode_token, make_access_token, make_refresh_token
from app.core.security.hashing import verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(body: LoginRequest, db: DBSession) -> TokenPair:
    q = select(User).where(User.email == body.email.lower().strip())
    user = (await db.execute(q)).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(403, "User disabled")

    access  = make_access_token(user.id, user.is_admin)
    refresh = make_refresh_token(user.id)
    return TokenPair(access_token=access, refresh_token=refresh.token, token_type="bearer")


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, db: DBSession) -> TokenPair:
    payload = decode_token(body.refresh_token, expected_type="refresh")
    sub = int(payload["sub"])
    user = await db.get(User, sub)
    if not user or not user.is_active:
        raise HTTPException(401, "Bad token")

    access  = make_access_token(user.id, user.is_admin)
    refresh = make_refresh_token(user.id)
    return TokenPair(access_token=access, refresh_token=refresh.token, token_type="bearer")


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> User:
    return user