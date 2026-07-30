"""IDS alert model."""
from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class Alert(Base, UUIDPKMixin, TimestampMixin):
    """A normalised alert from Suricata / Zeek / honeypot correlation."""

    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_severity_created", "severity", "created_at"),
        Index("ix_alerts_src_ip", "src_ip"),
    )

    source: Mapped[str] = mapped_column(String(20), nullable=False)  # suricata|zeek|honeypot
    signature: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..4
    src_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    dst_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    honeypot_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("honeypot_events.id", ondelete="SET NULL"),
        nullable=True,
    )