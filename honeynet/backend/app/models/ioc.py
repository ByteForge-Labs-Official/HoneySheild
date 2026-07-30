"""IOC + audit log models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import ARRAY, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IOC(Base):
    __tablename__ = "iocs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    kind:  Mapped[str] = mapped_column(String(16), nullable=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen:  Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    source: Mapped[Optional[str]] = mapped_column(String(64))
    tags:   Mapped[list[str]] = mapped_column(ARRAY(String(64)), default=list)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    actor_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    action:  Mapped[str] = mapped_column(String(64), nullable=False)
    target:  Mapped[Optional[str]] = mapped_column(String(255))
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    ip:      Mapped[Optional[str]] = mapped_column(INET)
    ts:      Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)