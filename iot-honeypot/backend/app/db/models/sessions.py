"""Session — a single attacker connection or attack campaign window.

A ``Session`` is created when the relay sees the first event from a
(``src_ip``, ``honeypot``, ``protocol``) tuple within the open-window. It
closes on inactivity (default 30 min). Events reference their session via
``events.session_id`` so the analyst can pivot from any single step to the
whole interaction.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class Session(Base, UUIDPKMixin, TimestampMixin):
    """An attacker session — bounded window of related events."""

    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_honeypot_started", "honeypot_id", "started_at"),
        Index("ix_sessions_src_ip_started", "src_ip", "started_at"),
        Index("ix_sessions_state", "state"),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_sessions_ended_after_started",
        ),
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    state: Mapped[str] = mapped_column(
        String(16), default="open", nullable=False
    )  # open|closed|timed_out|reaped
    src_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    src_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str] = mapped_column(String(16), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bytes_in: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bytes_out: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    commands_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    authenticated: Mapped[bool] = mapped_column(default=False, nullable=False)
    mitre_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)), default=list, nullable=False
    )

    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
    )
    honeypot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("honeypots.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Convenience: pull the related events in one round-trip
    # (events are linked back via events.session_id)