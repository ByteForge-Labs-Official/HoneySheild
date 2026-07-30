"""AI-generated insight attached to honeypot events."""
from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class AIInsight(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "ai_insights"
    __table_args__ = (
        Index("ix_insights_model_created", "model", "created_at"),
    )

    honeypot_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("honeypot_events.id", ondelete="CASCADE"),
        nullable=True,
    )
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    mitre_attack: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)), default=list, nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)