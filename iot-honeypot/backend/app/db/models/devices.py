"""Devices & Services — the inventory of physical/virtual assets under watch.

- ``Device`` represents an IoT endpoint or honeypot host (1:1 with ``Honeypot``
  is *not* enforced — a single device can host multiple honeypot profiles).
- ``Service`` is a port-protocol binding exposed by a device. A service is
  typically tied to a honeypot; the link is the polymorphic ``service_target``
  (honeypot_id nullable FK).
- A ``Device`` is also a ``NetworkAsset`` candidate (see ``network_assets.py``).
"""
from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, MACADDR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class Device(Base, UUIDPKMixin, TimestampMixin):
    """An IoT-style endpoint under surveillance or emulated by a honeypot."""

    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint("mac_address", name="uq_devices_mac"),
        Index("ix_devices_kind", "kind"),
        Index("ix_devices_owner", "owner_user_id"),
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_devices_risk_score_range",
        ),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    # 'camera' | 'router' | 'thermostat' | 'hub' | 'sensor' | '...' |
    # 'honeypot' (synthetic)
    mac_address: Mapped[str | None] = mapped_column(MACADDR, nullable=True)
    primary_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(32)), default=list, nullable=False
    )
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_at: Mapped[str | None] = mapped_column(
        String(40), nullable=True
    )  # free-text ISO until we add a real tz datetime; keeps DDL portable
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    services: Mapped[list["Service"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )


class Service(Base, UUIDPKMixin, TimestampMixin):
    """A protocol-port binding on a device (or a standalone service record)."""

    __tablename__ = "services"
    __table_args__ = (
        UniqueConstraint(
            "device_id", "protocol", "port", name="uq_services_device_proto_port"
        ),
        Index("ix_services_protocol", "protocol"),
        Index("ix_services_state", "state"),
    )

    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=True,
    )
    honeypot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("honeypots.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    protocol: Mapped[str] = mapped_column(String(16), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(
        String(16), default="open", nullable=False
    )  # open|filtered|closed|honeypot
    banner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tls: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    device: Mapped["Device | None"] = relationship(back_populates="services")