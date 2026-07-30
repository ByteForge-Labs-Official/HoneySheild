"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-28 00:00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("full_name", sa.String(120)),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("roles", postgresql.ARRAY(sa.String(32)), nullable=False, server_default="{}"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "honeypots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("vendor", sa.String(80)),
        sa.Column("host", sa.String(255), nullable=False),
        sa.Column("port", sa.Integer, nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("config", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_honeypots_kind", "honeypots", ["kind"])

    op.create_table(
        "honeypot_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("honeypot_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("honeypots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("protocol", sa.String(16), nullable=False),
        sa.Column("src_ip", postgresql.INET),
        sa.Column("src_port", sa.Integer),
        sa.Column("dst_port", sa.Integer),
        sa.Column("session_id", sa.String(128)),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("raw_size", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_events_honeypot_created", "honeypot_events", ["honeypot_id", "created_at"])
    op.create_index("ix_events_src_ip", "honeypot_events", ["src_ip"])

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("signature", sa.String(255), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("severity", sa.Integer, nullable=False),
        sa.Column("src_ip", postgresql.INET),
        sa.Column("dst_ip", postgresql.INET),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("raw", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("honeypot_event_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("honeypot_events.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_severity_created", "alerts", ["severity", "created_at"])
    op.create_index("ix_alerts_src_ip", "alerts", ["src_ip"])
    op.create_index("ix_alerts_signature", "alerts", ["signature"])

    op.create_table(
        "ai_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("honeypot_event_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("honeypot_events.id", ondelete="CASCADE")),
        sa.Column("model", sa.String(80), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("mitre_attack", postgresql.ARRAY(sa.String(16)), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_insights_model_created", "ai_insights", ["model", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_insights_model_created", table_name="ai_insights")
    op.drop_table("ai_insights")
    op.drop_index("ix_alerts_signature", table_name="alerts")
    op.drop_index("ix_alerts_src_ip", table_name="alerts")
    op.drop_index("ix_alerts_severity_created", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_events_src_ip", table_name="honeypot_events")
    op.drop_index("ix_events_honeypot_created", table_name="honeypot_events")
    op.drop_table("honeypot_events")
    op.drop_index("ix_honeypots_kind", table_name="honeypots")
    op.drop_table("honeypots")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")