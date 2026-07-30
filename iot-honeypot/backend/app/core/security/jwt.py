"""JWT encode/decode helpers and token payload schemas."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import jwt

from app.core.config import get_settings


@dataclass(slots=True, frozen=True)
class TokenPayload:
    sub: str
    exp: int
    iat: int
    type: str
    roles: tuple[str, ...] = ()
    jti: str | None = None


def _now() -> int:
    return int(time.time())


def _encode(payload: dict[str, Any]) -> str:
    return jwt.encode(
        payload,
        get_settings().jwt_secret.get_secret_value(),
        algorithm=get_settings().jwt_algorithm,
    )


def _decode(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        get_settings().jwt_secret.get_secret_value(),
        algorithms=[get_settings().jwt_algorithm],
    )


def create_access_token(
    *, subject: str, roles: list[str] | None = None, ttl_min: int | None = None
) -> str:
    s = get_settings()
    ttl = ttl_min or s.jwt_access_ttl_min
    now = _now()
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + ttl * 60,
        "type": "access",
        "roles": roles or [],
    }
    return _encode(payload)


def create_refresh_token(*, subject: str, ttl_days: int | None = None) -> str:
    s = get_settings()
    ttl = ttl_days or s.jwt_refresh_ttl_days
    now = _now()
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + ttl * 86_400,
        "type": "refresh",
        "roles": [],
    }
    return _encode(payload)


def decode_token(token: str) -> TokenPayload:
    raw = _decode(token)
    return TokenPayload(
        sub=raw["sub"],
        exp=raw["exp"],
        iat=raw["iat"],
        type=raw.get("type", "access"),
        roles=tuple(raw.get("roles") or ()),
        jti=raw.get("jti"),
    )