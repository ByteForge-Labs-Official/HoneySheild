"""Honeypot and honeypot-event models."""
from __future__ import annotations

import uuid

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class Honeypot(Base, UUIDPKMixin, TimestampMixin):
    """A deployed honeypot instance profile."""

    __tablename__ = "honeypots"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    vendor: Mapped[str | None] = mapped_column(String(80), nullable=True)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class HoneypotEvent(Base, UUIDPKMixin, TimestampMixin):
    """A single attacker interaction captured by a honeypot."""

    __tablename__ = "honeypot_events"
    __table_args__ = (
        Index("ix_events_honeypot_created", "honeypot_id", "created_at"),
        Index("ix_events_src_ip", "src_ip"),
    )

    honeypot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("honeypots.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    protocol: Mapped[str] = mapped_column(String(16), nullable=False)
    src_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    src_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    raw_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)