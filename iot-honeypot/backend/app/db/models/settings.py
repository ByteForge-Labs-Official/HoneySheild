"""Settings — key/value configuration with scoping.

A flat ``settings`` table is the simplest 3NF-correct design for runtime
configuration that doesn't need to be in the same row as another entity:

- ``scope`` ('global' | 'user' | 'honeypot' | 'device') + ``scope_id``
  lets us store the same key at multiple levels. Lookups fall back from the
  narrowest scope to the widest (``user`` → ``global``).
- ``value_json`` keeps values typed without 12 typed columns.
- ``is_secret`` lets the UI redact values and the API refuse to log them.

Versioned through ``version`` so the audit log can show what changed.
"""
from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class Setting(Base, UUIDPKMixin, TimestampMixin):
    """A single scoped configuration key/value pair."""

    __tablename__ = "settings"
    __table_args__ = (
        # Same key may exist once per scope+scope_id; ``scope='global'`` ⇒ scope_id NULL.
        UniqueConstraint(
            "scope", "scope_id", "key", name="uq_settings_scope_key"
        ),
        Index("ix_settings_scope_key", "scope", "key"),
        CheckConstraint(
            "scope IN ('global','user','honeypot','device','service')",
            name="ck_settings_scope_enum",
        ),
    )

    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value_json: Mapped[object] = mapped_column(JSONB, nullable=False)
    value_type: Mapped[str] = mapped_column(
        String(16), default="string", nullable=False
    )  # string|int|float|bool|json
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )