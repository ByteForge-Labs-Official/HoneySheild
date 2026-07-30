"""Attack + Event models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import ARRAY, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Attack(Base):
    __tablename__ = "attacks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    protocol: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at:   Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    success:    Mapped[bool] = mapped_column(Boolean, default=False)
    severity:   Mapped[str] = mapped_column(String(16), default="info")
    payload:    Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    mitre_tags: Mapped[list[str]] = mapped_column(ARRAY(String(80)), default=list)
    src_ip:     Mapped[str] = mapped_column(INET, nullable=False)
    dst_port:   Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    attack_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("attacks.id"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="info")
    payload:  Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    src_ip:   Mapped[Optional[str]] = mapped_column(INET)
    dst_ip:   Mapped[Optional[str]] = mapped_column(INET)
    raw:      Mapped[Optional[str]] = mapped_column(Text)