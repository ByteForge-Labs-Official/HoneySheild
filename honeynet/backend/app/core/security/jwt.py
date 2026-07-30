"""JWT helpers — short-lived access tokens, opaque refresh tokens cached in Redis."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config.settings import get_settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def make_access_token(subject: str, claims: dict | None = None) -> str:
    s = get_settings()
    payload = {
        "sub": subject,
        "type": "access",
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(minutes=s.jwt_access_ttl_min)).timestamp()),
        **({} if claims is None else claims),
    }
    return jwt.encode(payload, s.jwt_secret.get_secret_value(), algorithm=s.jwt_alg)


def make_refresh_token(subject: str) -> tuple[str, str]:
    """Return (token_id, jwt).  The token_id is also stored in Redis so we can revoke it."""
    s = get_settings()
    jti = secrets.token_urlsafe(32)
    payload = {
        "sub": subject,
        "jti": jti,
        "type": "refresh",
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(days=s.jwt_refresh_ttl_days)).timestamp()),
    }
    return jti, jwt.encode(payload, s.jwt_secret.get_secret_value(), algorithm=s.jwt_alg)


def decode_token(token: str, expected_type: str) -> dict | None:
    s = get_settings()
    try:
        payload = jwt.decode(
            token,
            s.jwt_secret.get_secret_value(),
            algorithms=[s.jwt_alg],
            options={"require": ["exp", "iat", "sub", "type"]},
        )
    except jwt.PyJWTError:
        return None
    return payload if payload.get("type") == expected_type else None
