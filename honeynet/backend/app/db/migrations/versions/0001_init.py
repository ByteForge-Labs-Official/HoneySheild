"""initial schema

Revision ID: 0001_init
Revises:
Create Date: 2026-07-28 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext;")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(254), unique=True, nullable=False),
        sa.Column("username", sa.String(64), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_admin",  sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("vendor", sa.String(64), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("firmware_version", sa.String(32), nullable=False),
        sa.Column("bait_ports", postgresql.ARRAY(sa.Integer()), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(16), nullable=False, server_default="online"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("remote_ip", postgresql.INET(), nullable=False),
        sa.Column("src_port", sa.Integer()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("bytes_in", sa.BigInteger(), server_default="0"),
        sa.Column("bytes_out", sa.BigInteger(), server_default="0"),
        sa.Column("country_iso", sa.String(2)),
        sa.Column("asn", sa.String(64)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("transport", sa.String(16), nullable=False),
    )
    op.create_index("ix_sessions_remote_ip", "sessions", ["remote_ip"])
    op.create_index("ix_sessions_started_at", "sessions", ["started_at"])

    op.create_table(
        "attacks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("protocol", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("success", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("severity", sa.String(16), server_default="info"),
        sa.Column("payload", postgresql.JSONB(), server_default="{}"),
        sa.Column("mitre_tags", postgresql.ARRAY(sa.String(80)), server_default="{}"),
        sa.Column("src_ip", postgresql.INET(), nullable=False),
        sa.Column("dst_port", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_attacks_protocol", "attacks", ["protocol"])
    op.create_index("ix_attacks_src_ip",    "attacks", ["src_ip"])
    op.create_index("ix_attacks_started_at","attacks", ["started_at"])

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("attack_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attacks.id"), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), server_default="info"),
        sa.Column("payload", postgresql.JSONB(), server_default="{}"),
        sa.Column("src_ip", postgresql.INET()),
        sa.Column("dst_ip", postgresql.INET()),
        sa.Column("raw", sa.Text()),
    )
    op.create_index("ix_events_attack_id", "events", ["attack_id"])
    op.create_index("ix_events_ts",        "events", ["ts"])
    op.create_index("ix_events_kind",      "events", ["kind"])

    op.create_table(
        "iocs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),  # ip|domain|hash|url|email
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confidence", sa.Float(), server_default="0.5"),
        sa.Column("source", sa.String(64)),
        sa.Column("tags", postgresql.ARRAY(sa.String(64)), server_default="{}"),
    )
    op.create_index("ix_iocs_value",  "iocs", ["value"])
    op.create_index("ix_iocs_kind",   "iocs", ["kind"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target", sa.String(255)),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("ip", postgresql.INET()),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_actor", "audit_log", ["actor_id"])
    op.create_index("ix_audit_ts",    "audit_log", ["ts"])

    # Materialized views for analytics
    op.execute("""
        CREATE MATERIALIZED VIEW mv_attacks_per_min AS
        SELECT date_trunc('minute', started_at) AS bucket,
               protocol,
               count(*) AS attacks,
               count(DISTINCT src_ip) AS distinct_ips
        FROM attacks
        GROUP BY 1, 2;
    """)
    op.execute("CREATE INDEX ix_mv_attacks_per_min_bucket ON mv_attacks_per_min (bucket);")

    op.execute("""
        CREATE MATERIALIZED VIEW mv_top_offenders AS
        SELECT src_ip, count(*) AS hits, max(started_at) AS last_seen
        FROM attacks
        GROUP BY src_ip ORDER BY hits DESC LIMIT 1000;
    """)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_top_offenders;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_attacks_per_min;")
    op.drop_table("audit_log")
    op.drop_table("iocs")
    op.drop_table("events")
    op.drop_table("attacks")
    op.drop_table("sessions")
    op.drop_table("devices")
    op.drop_table("users")