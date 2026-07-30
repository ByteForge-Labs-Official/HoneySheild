"""Honeypot DTOs."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress


class HoneypotBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    kind: str = Field(min_length=2, max_length=40)
    vendor: str | None = Field(default=None, max_length=80)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class HoneypotCreate(HoneypotBase):
    pass


class HoneypotUpdate(BaseModel):
    vendor: str | None = None
    host: str | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    enabled: bool | None = None
    config: dict[str, Any] | None = None


class HoneypotOut(HoneypotBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class HoneypotEventOut(BaseModel):
    id: str
    honeypot_id: str
    event_type: str
    protocol: str
    src_ip: str | None
    src_port: int | None
    dst_port: int | None
    session_id: str | None
    payload: dict[str, Any]
    raw_size: int
    created_at: datetime