"""Schemas — devices."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    kind: str = Field(..., min_length=2, max_length=32)
    vendor: str = Field(..., min_length=2, max_length=64)
    model:  str = Field(..., min_length=2, max_length=64)
    firmware_version: str = Field(..., min_length=2, max_length=32)
    bait_ports: list[int] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    kind: str | None = None
    vendor: str | None = None
    model:  str | None = None
    firmware_version: str | None = None
    bait_ports: list[int] | None = None
    metadata: dict[str, Any] | None = None
    status: str | None = Field(default=None, pattern="^(online|offline|degraded)$")


class DeviceOut(DeviceBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class DeviceControl(BaseModel):
    """Send a command to the bait device via MQTT."""
    topic:   str = Field(..., max_length=255)
    payload: dict[str, Any]
    retain:  bool = False