"""Alert DTO."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: str
    source: str
    signature: str
    category: str
    severity: int
    src_ip: str | None
    dst_ip: str | None
    confidence: float
    raw: dict[str, Any]
    honeypot_event_id: str | None
    created_at: datetime