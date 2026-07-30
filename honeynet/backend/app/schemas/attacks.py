"""Schemas — attacks & events."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    attack_id: UUID
    ts: datetime
    kind: str
    severity: str
    payload: dict[str, Any]
    src_ip: str | None
    dst_ip: str | None


class AttackBase(BaseModel):
    protocol: str = Field(..., max_length=16)
    started_at: datetime
    severity:   str = Field(default="info")
    mitre_tags: list[str] = Field(default_factory=list)


class AttackOut(AttackBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    session_id: UUID
    ended_at: datetime | None
    success: bool
    src_ip: str
    dst_port: int | None
    created_at: datetime


class AttackDetail(AttackOut):
    events: list[EventOut] = Field(default_factory=list)


class AttackPage(BaseModel):
    items: list[AttackOut]
    total: int
    page:  int
    size:  int


class AttackQuery(BaseModel):
    protocol:    list[str] | None = None
    severity:    list[str] | None = None
    src_ip:      str | None = None
    country_iso: str | None = None
    since:       datetime | None = None
    until:       datetime | None = None
    page:  int = 1
    size:  int = Field(default=50, le=500)
    sort:  str = Field(default="-started_at")