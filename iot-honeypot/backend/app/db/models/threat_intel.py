"""Threat Intelligence + Malware metadata + Indicators of Compromise.

Three coupled tables:

- ``ThreatIntel`` — a *feed entry* (one row per MISP/STIX/CSV-imported record).
- ``MalwareMetadata`` — a *malware family/sample* reference data row.
- ``IOC`` — an extracted atomic indicator (ip, domain, hash, url, mutex, ...).

``IOC`` has an M:N link to both ``ThreatIntel`` (source intel that mentioned it)
and ``MalwareMetadata`` (malware that uses it). A separate ``ioc_links`` table
implements the M:N so we don't denormalise; that file lives in
``indicators_of_compromise.py``.
"""
from __future__ import annotations

import uuid
from datetime import datetime

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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class ThreatIntel(Base, UUIDPKMixin, TimestampMixin):
    """A single record from an external threat-intel feed."""

    __tablename__ = "threat_intelligence"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_threat_source_extid"),
        Index("ix_threat_source_published", "source", "published_at"),
        Index("ix_threat_tlp", "tlp"),
        CheckConstraint(
            "tlp IN ('white','green','amber','amber+strict','red')",
            name="ck_threat_tlp_enum",
        ),
    )

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    # 'misp' | 'stix-taxii' | 'abuse.ch' | 'otx' | 'manual'
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tlp: Mapped[str] = mapped_column(
        String(16), default="amber", nullable=False
    )  # Traffic Light Protocol
    confidence: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    severity: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )  # low|medium|high|critical
    mitre_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)), default=list, nullable=False
    )
    references: Mapped[list[str]] = mapped_column(
        ARRAY(String(512)), default=list, nullable=False
    )
    raw: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class MalwareMetadata(Base, UUIDPKMixin, TimestampMixin):
    """Reference data for a malware family or specific sample."""

    __tablename__ = "malware_metadata"
    __table_args__ = (
        Index("ix_malware_family", "family"),
        Index("ix_malware_type", "malware_type"),
        UniqueConstraint(
            "sha256", name="uq_malware_sha256"
        ),
        CheckConstraint(
            "malware_type IN ('virus','worm','trojan','ransomware',"
            "'spyware','rootkit','botnet','apt','other')",
            name="ck_malware_type_enum",
        ),
    )

    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    sha1: Mapped[str | None] = mapped_column(String(40), nullable=True)
    md5: Mapped[str | None] = mapped_column(String(32), nullable=True)
    family: Mapped[str | None] = mapped_column(String(120), nullable=True)
    malware_type: Mapped[str] = mapped_column(
        String(32), default="other", nullable=False
    )
    aliases: Mapped[list[str]] = mapped_column(
        ARRAY(String(64)), default=list, nullable=False
    )
    first_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    severity: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )  # low|medium|high|critical
    mitre_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)), default=list, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)