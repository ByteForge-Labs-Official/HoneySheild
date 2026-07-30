"""Notifications — outbound channel messages (email, Slack, webhook, ...).

The ``Notification`` row is *outbound* — i.e. "we sent this". The companion
``alerts`` table is the *inbound event* that triggered the notification.
We keep them separate so a notification can be sent without an alert
(report reminders, scheduled task outcomes) and an alert can exist without
having triggered a notification (rate-limited, suppressed).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class Notification(Base, UUIDPKMixin, TimestampMixin):
    """A single outbound notification message."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notif_channel_status_ts", "channel", "status", "scheduled_at"),
        Index("ix_notif_user_ts", "recipient_user_id", "scheduled_at"),
        CheckConstraint(
            "channel IN ('email','slack','webhook','pagerduty','sms','in_app')",
            name="ck_notif_channel_enum",
        ),
        CheckConstraint(
            "status IN ('queued','sent','failed','cancelled','rate_limited')",
            name="ck_notif_status_enum",
        ),
    )

    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default="queued", nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    # 1 (low) ... 5 (critical)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    target: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # email addr, slack channel id, webhook url, ...
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    alert_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="SET NULL"),
        nullable=True,
    )
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="SET NULL"),
        nullable=True,
    )