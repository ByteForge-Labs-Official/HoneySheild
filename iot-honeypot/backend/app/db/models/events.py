"""Event-log core: the append-only stream of attacker interactions.

Two tables are kept deliberately separate:

- ``Event``   — the *normalised* action log (a single attacker step).
- ``Log``     — the *raw* text blob from the device/honeypot, for forensics.

The split avoids storing huge raw payloads inside the row that Grafana
aggregates: Grafana sees only ``Event``, while ``Log`` is searchable by text.

The relay ships data into ``Event`` (and links a ``Log`` row when the source
was a log line). ``HoneypotEvent`` (existing) is kept as a per-protocol
detail row; ``Event`` is the cross-protocol ledger.
"""
from __future__ import annotations

import uuid

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class Event(Base, UUIDPKMixin, TimestampMixin):
    """A single normalised attacker-action record — the *ledger* of the system."""

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_ts", "ts"),
        Index("ix_events_source_ip_ts", "src_ip", "ts"),
        Index("ix_events_kind_ts", "kind", "ts"),
        Index("ix_events_severity_ts", "severity", "ts"),
        # Designed to be a TimescaleDB hypertable in production. The
        # ``ts`` column is the time partitioning key.
        CheckConstraint(
            "severity BETWEEN 1 AND 5", name="ck_events_severity_range"
        ),
    )

    ts: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    # login_attempt | cmd_exec | http_request | rtsp_describe |
    # mqtt_subscribe | modbus_read | file_download | scan | ...
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol: Mapped[str | None] = mapped_column(String(16), nullable=True)
    src_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    src_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dst_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    username: Mapped[str | None] = mapped_column(String(120), nullable=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    command: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_size: Mapped[int] = mapped_column(
        BigInteger, default=0, nullable=False
    )
    mitre_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)), default=list, nullable=False
    )
    success: Mapped[bool | None] = mapped_column(
        # null = not applicable (e.g. passive scan)
        # True/False = clear outcome for login/cmd events.
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    extra: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True,
    )
    honeypot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("honeypots.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("logs.id", ondelete="SET NULL"),
        nullable=True,
    )


class Log(Base, UUIDPKMixin, TimestampMixin):
    """A raw log line/record from a device or honeypot, kept for forensics."""

    __tablename__ = "logs"
    __table_args__ = (
        Index("ix_logs_source_ts", "source", "ts"),
        Index("ix_logs_level_ts", "level", "ts"),
    )

    ts: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    # 'honeypot:ssh' | 'honeypot:http' | 'suricata' | 'zeek' | 'system'
    level: Mapped[str] = mapped_column(
        String(16), default="info", nullable=False
    )  # debug|info|warn|error|critical
    message: Mapped[str] = mapped_column(Text, nullable=False)
    structured: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
    )
    honeypot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("honeypots.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="SET NULL"),
        nullable=True,
    )