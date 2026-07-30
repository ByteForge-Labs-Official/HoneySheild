"""Reports — scheduled/on-demand analyst deliverables.

A ``Report`` is a row describing a generated deliverable (PDF, CSV, JSON,
HTML). The actual artifact is stored on disk and referenced by ``artifact_uri``;
only metadata lives in the DB so we don't bloat Postgres with blob data.
"""
from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class Report(Base, UUIDPKMixin, TimestampMixin):
    """A scheduled or on-demand analyst report."""

    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_status", "status"),
        Index("ix_reports_kind_generated", "kind", "generated_at"),
        CheckConstraint(
            "status IN ('pending','running','completed','failed','expired')",
            name="ck_reports_status_enum",
        ),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    # 'executive_summary' | 'ioc_dump' | 'top_offenders' |
    # 'incident_postmortem' | 'compliance'
    status: Mapped[str] = mapped_column(
        String(16), default="pending", nullable=False
    )
    format: Mapped[str] = mapped_column(
        String(8), default="pdf", nullable=False
    )  # pdf|csv|json|html
    period_start: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    generated_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    artifact_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(32)), default=list, nullable=False
    )

    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )