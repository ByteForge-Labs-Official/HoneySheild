"""Auth DTOs."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    username: str = Field(min_length=3, max_length=128)
    password: str = Field(min_length=8, max_length=256)


class RefreshIn(BaseModel):
    refresh_token: str


class RegisterIn(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=256)
    full_name: str | None = Field(default=None, max_length=120)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int