"""IOCs (Indicators of Compromise) and their links.

``IOC`` is the extracted atomic value (one row per observable). It uses a
**polymorphic value column**: ``value`` is the string form, ``value_inet`` /
``value_cidr`` / ``value_hash`` are typed projections for query speed.

M:N links to ``threat_intelligence`` and ``malware_metadata`` are kept in
``ioc_threat_intel`` and ``ioc_malware`` respectively, with first/last-seen
timestamps on the link so we can compute IOC staleness.
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
from sqlalchemy.dialects.postgresql import CIDR, INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class IOC(Base, UUIDPKMixin, TimestampMixin):
    """A single observable (ip, domain, hash, url, mutex, ...)."""

    __tablename__ = "indicators_of_compromise"
    __table_args__ = (
        # Same value may appear once per (kind, source).
        UniqueConstraint("kind", "value", "source", name="uq_ioc_kind_value_source"),
        Index("ix_ioc_kind_value", "kind", "value"),
        Index("ix_ioc_value_inet", "value_inet"),
        Index("ix_ioc_first_seen", "first_seen_at"),
        CheckConstraint(
            "kind IN ('ip','domain','url','sha256','sha1','md5','email',"
            "'mutex','filepath','registry','yara','cidr','asn')",
            name="ck_ioc_kind_enum",
        ),
    )

    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    value: Mapped[str] = mapped_column(String(2048), nullable=False)
    # Typed projections — populated on insert based on ``kind``.
    value_inet: Mapped[str | None] = mapped_column(INET, nullable=True)
    value_cidr: Mapped[str | None] = mapped_column(CIDR, nullable=True)
    value_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    confidence: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    severity: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )  # low|medium|high|critical
    tlp: Mapped[str] = mapped_column(String(16), default="amber", nullable=False)
    first_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    # 'relay' | 'misp' | 'abuse.ch' | 'manual' | 'correlator'
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    references: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    false_positive: Mapped[bool] = mapped_column(default=False, nullable=False)


class IOCThreatIntelLink(Base):
    """M:N link between an IOC and a ThreatIntel record that mentions it."""

    __tablename__ = "ioc_threat_intel"
    __table_args__ = (
        UniqueConstraint("ioc_id", "threat_intel_id", name="uq_ioc_threat"),
        Index("ix_ioc_threat_ioc", "ioc_id"),
        Index("ix_ioc_threat_ti", "threat_intel_id"),
    )

    ioc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indicators_of_compromise.id", ondelete="CASCADE"),
        primary_key=True,
    )
    threat_intel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threat_intelligence.id", ondelete="CASCADE"),
        primary_key=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)


class IOCMalwareLink(Base):
    """M:N link between an IOC and a MalwareMetadata row that uses it."""

    __tablename__ = "ioc_malware"
    __table_args__ = (
        UniqueConstraint("ioc_id", "malware_id", name="uq_ioc_malware"),
        Index("ix_ioc_malware_ioc", "ioc_id"),
        Index("ix_ioc_malware_malware", "malware_id"),
    )

    ioc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indicators_of_compromise.id", ondelete="CASCADE"),
        primary_key=True,
    )
    malware_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("malware_metadata.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(
        String(32), default="indicator", nullable=False
    )  # indicator|dropper_url|c2|hash|...
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)