"""Schemas — analytics + threats."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TopIp(BaseModel):
    src_ip: str
    hits:   int
    last_seen: datetime


class TimelineBucket(BaseModel):
    bucket:    datetime
    protocol:  str
    attacks:   int
    distinct_ips: int


class GeoPoint(BaseModel):
    country_iso: str
    country_name: str
    lat: float
    lon: float
    hits: int


class MitreTag(BaseModel):
    tag:        str
    count:      int
    last_seen:  datetime


class IOCOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    value: str
    kind:  str
    first_seen: datetime
    last_seen:  datetime
    confidence: float
    source: str | None
    tags:   list[str]


class ThreatFeedback(BaseModel):
    ioc_id: UUID
    label:  str = Field(..., pattern="^(true_positive|false_positive|needs_review)$")
    notes:  str | None = Field(default=None, max_length=4000)


class LiveAttackMessage(BaseModel):
    kind: str               # "attack" | "event" | "iocs"
    payload: dict[str, Any] | list[Any]


class HealthReport(BaseModel):
    status: str             # "ok" | "degraded" | "down"
    components: dict[str, dict[str, Any]]