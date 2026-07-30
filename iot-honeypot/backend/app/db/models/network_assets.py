"""Network assets — the network-graph layer.

While ``Device`` models *what something is* (a camera, a router, a hub),
``NetworkAsset`` models *where it sits on the network*. A single device can
have several ``NetworkAsset`` rows over time (DHCP roaming, IP migration,
multi-NIC).

The link table ``network_asset_relationships`` builds a directed graph that
PowerShell-of-the-DB queries can walk with recursive CTEs.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, CIDR, INET, JSONB, MACADDR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class NetworkAsset(Base, UUIDPKMixin, TimestampMixin):
    """A network-visible position: IP, MAC, ASN, geo."""

    __tablename__ = "network_assets"
    __table_args__ = (
        # Same (device, ip, since) tuple is unique.
        UniqueConstraint(
            "device_id", "ip_address", "since",
            name="uq_netasset_device_ip_since",
        ),
        Index("ix_netasset_ip", "ip_address"),
        Index("ix_netasset_asn", "asn"),
        Index("ix_netasset_country", "country_code"),
    )

    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=True,
    )
    ip_address: Mapped[str] = mapped_column(INET, nullable=False)
    mac_address: Mapped[str | None] = mapped_column(MACADDR, nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subnet: Mapped[str | None] = mapped_column(CIDR, nullable=True)
    asn: Mapped[int | None] = mapped_column(Integer, nullable=True)
    asn_org: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_external: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_tor_exit: Mapped[bool] = mapped_column(default=False, nullable=False)
    reputation_score: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # 0..100, higher = worse
    since: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(32)), default=list, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class NetworkAssetRelationship(Base):
    """Directed graph edge between two ``NetworkAsset`` rows."""

    __tablename__ = "network_asset_relationships"
    __table_args__ = (
        UniqueConstraint(
            "src_asset_id", "dst_asset_id", "kind",
            name="uq_rel_src_dst_kind",
        ),
        Index("ix_rel_src", "src_asset_id"),
        Index("ix_rel_dst", "dst_asset_id"),
        Index("ix_rel_kind", "kind"),
        CheckConstraint(
            "src_asset_id <> dst_asset_id",
            name="ck_rel_no_self_loop",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    src_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("network_assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    dst_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("network_assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    # 'talks_to' | 'routes_via' | 'resolves_to' | 'mirrors'
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_observed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_observed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extra: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)