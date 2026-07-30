"""Auth routes."""
from __future__ import annotations

from fastapi import APIRouter

from app.apideps.auth import get_current_user
from app.db.session import DbSession
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenOut
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenOut, summary="Username/password login")
async def login(payload: LoginIn, session: DbSession) -> TokenOut:
    return await AuthService(session).login(username=payload.username, password=payload.password)


@router.post("/refresh", response_model=TokenOut, summary="Refresh access token")
async def refresh(payload: RefreshIn, session: DbSession) -> TokenOut:
    return await AuthService(session).refresh(refresh_token=payload.refresh_token)


@router.post("/register", response_model=TokenOut, summary="Register a new user")
async def register(payload: RegisterIn, session: DbSession) -> TokenOut:
    return await AuthService(session).register(
        email=payload.email,
        username=payload.username,
        password=payload.password,
        full_name=payload.full_name,
    )


@router.get("/me", summary="Current authenticated user")
async def me(user: dict = get_current_user) -> dict:
    return {k: v for k, v in user.items() if k != "hashed_password"}