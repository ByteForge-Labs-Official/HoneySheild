"""Audit Logs — append-only trail of operator actions.

Distinct from ``Log`` (which captures attacker traffic) and ``Event``
(which captures attacker steps). Every privileged API call writes one
``AuditLog`` row. ``CHAIN`` keeps the linked sequence of related actions.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import UUIDPKMixin
from app.db.session import Base


class AuditLog(UUIDPKMixin):
    """Append-only audit trail of operator actions."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_user_ts", "user_id", "ts"),
        Index("ix_audit_action_ts", "action", "ts"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
        CheckConstraint(
            "outcome IN ('success','failure','denied','error')",
            name="ck_audit_outcome_enum",
        ),
    )

    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    # 'user.create' | 'role.assign' | 'alert.ack' | 'report.delete' | ...
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    outcome: Mapped[str] = mapped_column(
        String(16), default="success", nullable=False
    )
    source_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    chain: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # request_id of the originating action
    before: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    after: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)