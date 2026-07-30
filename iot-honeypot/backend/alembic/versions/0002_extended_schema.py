"""extended schema: roles, permissions, devices, services, events, logs,
sessions, reports, threat_intel, malware_metadata, iocs, network_assets,
audit_logs, notifications, settings.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-28 12:00:00

Notes:
- Existing tables (``users``, ``honeypots``, ``honeypot_events``, ``alerts``,
  ``ai_insights``) are not touched.
- The ``events`` table is built so a TimescaleDB hypertable can be created
  later with::
      SELECT create_hypertable('events', 'ts', chunk_time_interval => INTERVAL '1 hour');
- All foreign keys use ``ON DELETE`` rules consistent with the source
  semantics: ``CASCADE`` for owned children, ``SET NULL`` for loose refs.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    inet = postgresql.INET
    cidr = postgresql.CIDR
    mac = postgresql.MACADDR
    jsonb = postgresql.JSONB
    array_str = postgresql.ARRAY(sa.String)

    # ---------------------------------------------------------------- RBAC
    op.create_table(
        "roles",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("priority", sa.Integer, nullable=False, server_default="100"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_index("ix_roles_name", "roles", ["name"])

    op.create_table(
        "permissions",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("code", sa.String(96), nullable=False),
        sa.Column("resource", sa.String(64), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"])
    op.create_index("ix_permissions_resource", "permissions", ["resource"])

    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            uuid,
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "granted_by",
            uuid,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles"),
    )
    op.create_index("ix_user_roles_user", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role", "user_roles", ["role_id"])

    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            uuid,
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            uuid,
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
    )
    op.create_index("ix_role_permissions_role", "role_permissions", ["role_id"])
    op.create_index(
        "ix_role_permissions_permission", "role_permissions", ["permission_id"]
    )

    # ------------------------------------------------------------ DEVICES
    op.create_table(
        "devices",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("vendor", sa.String(80)),
        sa.Column("model", sa.String(120)),
        sa.Column("firmware_version", sa.String(64)),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("mac_address", mac),
        sa.Column("primary_ip", inet),
        sa.Column("tags", array_str, nullable=False, server_default="{}"),
        sa.Column("risk_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_seen_at", sa.String(40)),
        sa.Column("metadata", jsonb, nullable=False, server_default="{}"),
        sa.Column(
            "owner_user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("mac_address", name="uq_devices_mac"),
        sa.CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_devices_risk_score_range",
        ),
    )
    op.create_index("ix_devices_kind", "devices", ["kind"])
    op.create_index("ix_devices_owner", "devices", ["owner_user_id"])

    op.create_table(
        "services",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "device_id",
            uuid,
            sa.ForeignKey("devices.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "honeypot_id",
            uuid,
            sa.ForeignKey("honeypots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("protocol", sa.String(16), nullable=False),
        sa.Column("port", sa.Integer, nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="open"),
        sa.Column("banner", sa.String(255)),
        sa.Column("version", sa.String(64)),
        sa.Column("tls", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("description", sa.Text),
        sa.Column("config", jsonb, nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "device_id", "protocol", "port", name="uq_services_device_proto_port"
        ),
    )
    op.create_index("ix_services_protocol", "services", ["protocol"])
    op.create_index("ix_services_state", "services", ["state"])

    # ------------------------------------------------------------ SESSIONS (before events — events.session_id FKs sessions)
    op.create_table(
        "sessions",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("state", sa.String(16), nullable=False, server_default="open"),
        sa.Column("src_ip", inet),
        sa.Column("src_port", sa.Integer),
        sa.Column("protocol", sa.String(16), nullable=False),
        sa.Column("user_agent", sa.String(512)),
        sa.Column("bytes_in", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("bytes_out", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("commands_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("authenticated", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("mitre_tags", array_str, nullable=False, server_default="{}"),
        sa.Column(
            "device_id",
            uuid,
            sa.ForeignKey("devices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "honeypot_id",
            uuid,
            sa.ForeignKey("honeypots.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_sessions_ended_after_started",
        ),
    )
    op.create_index(
        "ix_sessions_honeypot_started", "sessions", ["honeypot_id", "started_at"]
    )
    op.create_index(
        "ix_sessions_src_ip_started", "sessions", ["src_ip", "started_at"]
    )
    op.create_index("ix_sessions_state", "sessions", ["state"])

    # ------------------------------------------------------------ LOGS (no FK to events — events.log_id FK added later, after events exists)
    op.create_table(
        "logs",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("level", sa.String(16), nullable=False, server_default="info"),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("structured", jsonb, nullable=False, server_default="{}"),
        sa.Column(
            "device_id",
            uuid,
            sa.ForeignKey("devices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "honeypot_id",
            uuid,
            sa.ForeignKey("honeypots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "event_id",
            uuid,
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_logs_source_ts", "logs", ["source", "ts"])
    op.create_index("ix_logs_level_ts", "logs", ["level", "ts"])

    # --------------------------------------------------- EVENTS (FK to logs added after both tables exist)
    op.create_table(
        "events",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("severity", sa.Integer, nullable=False),
        sa.Column("protocol", sa.String(16)),
        sa.Column("src_ip", inet),
        sa.Column("src_port", sa.Integer),
        sa.Column("dst_ip", inet),
        sa.Column("dst_port", sa.Integer),
        sa.Column("user_agent", sa.String(512)),
        sa.Column("username", sa.String(120)),
        sa.Column("password", sa.String(255)),
        sa.Column("command", sa.Text),
        sa.Column("payload_size", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("mitre_tags", array_str, nullable=False, server_default="{}"),
        sa.Column("success", sa.Boolean),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("extra", jsonb, nullable=False, server_default="{}"),
        sa.Column(
            "device_id",
            uuid,
            sa.ForeignKey("devices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "service_id",
            uuid,
            sa.ForeignKey("services.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "honeypot_id",
            uuid,
            sa.ForeignKey("honeypots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "session_id",
            uuid,
            sa.ForeignKey("sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "log_id",
            uuid,
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("severity BETWEEN 1 AND 5", name="ck_events_severity_range"),
    )
    op.create_index("ix_events_ts", "events", ["ts"])
    op.create_index("ix_events_source_ip_ts", "events", ["src_ip", "ts"])
    op.create_index("ix_events_kind_ts", "events", ["kind", "ts"])
    op.create_index("ix_events_severity_ts", "events", ["severity", "ts"])

    # Now wire the cross-FKs (events.log_id -> logs.id, logs.event_id -> events.id).
    op.create_foreign_key(
        "fk_events_log_id_logs",
        source_table="events",
        referent_table="logs",
        local_cols=["log_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_logs_event_id_events",
        source_table="logs",
        referent_table="events",
        local_cols=["event_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )

    # NOTE: `events.attack` (created in deploy/postgres/init/02-extensions.sql) is
    # the TimescaleDB hypertable for raw attack ingest. The `events` table here is
    # the canonical, FK-rich model used by the API — it is *not* a hypertable.

    # --------------------------------------------------- THREAT INTEL etc
    op.create_table(
        "threat_intelligence",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("tlp", sa.String(16), nullable=False, server_default="amber"),
        sa.Column("confidence", sa.Integer, nullable=False, server_default="50"),
        sa.Column("severity", sa.String(16)),
        sa.Column("mitre_tags", array_str, nullable=False, server_default="{}"),
        sa.Column("references", postgresql.ARRAY(sa.String(512)), nullable=False, server_default="{}"),
        sa.Column("raw", jsonb, nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("source", "external_id", name="uq_threat_source_extid"),
        sa.CheckConstraint(
            "tlp IN ('white','green','amber','amber+strict','red')",
            name="ck_threat_tlp_enum",
        ),
    )
    op.create_index(
        "ix_threat_source_published", "threat_intelligence", ["source", "published_at"]
    )
    op.create_index("ix_threat_tlp", "threat_intelligence", ["tlp"])

    op.create_table(
        "malware_metadata",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("sha1", sa.String(40)),
        sa.Column("md5", sa.String(32)),
        sa.Column("family", sa.String(120)),
        sa.Column("malware_type", sa.String(32), nullable=False, server_default="other"),
        sa.Column("aliases", array_str, nullable=False, server_default="{}"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True)),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("file_size", sa.BigInteger),
        sa.Column("file_type", sa.String(64)),
        sa.Column("severity", sa.String(16)),
        sa.Column("mitre_tags", array_str, nullable=False, server_default="{}"),
        sa.Column("notes", sa.Text),
        sa.Column("raw", jsonb, nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("sha256", name="uq_malware_sha256"),
        sa.CheckConstraint(
            "malware_type IN ('virus','worm','trojan','ransomware',"
            "'spyware','rootkit','botnet','apt','other')",
            name="ck_malware_type_enum",
        ),
    )
    op.create_index("ix_malware_family", "malware_metadata", ["family"])
    op.create_index("ix_malware_type", "malware_metadata", ["malware_type"])

    op.create_table(
        "indicators_of_compromise",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("value", sa.String(2048), nullable=False),
        sa.Column("value_inet", inet),
        sa.Column("value_cidr", cidr),
        sa.Column("value_hash", sa.String(64)),
        sa.Column("confidence", sa.Integer, nullable=False, server_default="50"),
        sa.Column("severity", sa.String(16)),
        sa.Column("tlp", sa.String(16), nullable=False, server_default="amber"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True)),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("references", jsonb, nullable=False, server_default="[]"),
        sa.Column("raw", jsonb, nullable=False, server_default="{}"),
        sa.Column(
            "false_positive",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("kind", "value", "source", name="uq_ioc_kind_value_source"),
        sa.CheckConstraint(
            "kind IN ('ip','domain','url','sha256','sha1','md5','email',"
            "'mutex','filepath','registry','yara','cidr','asn')",
            name="ck_ioc_kind_enum",
        ),
    )
    op.create_index("ix_ioc_kind_value", "indicators_of_compromise", ["kind", "value"])
    op.create_index(
        "ix_ioc_value_inet", "indicators_of_compromise", ["value_inet"]
    )
    op.create_index(
        "ix_ioc_first_seen", "indicators_of_compromise", ["first_seen_at"]
    )

    op.create_table(
        "ioc_threat_intel",
        sa.Column(
            "ioc_id",
            uuid,
            sa.ForeignKey("indicators_of_compromise.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "threat_intel_id",
            uuid,
            sa.ForeignKey("threat_intelligence.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.5"),
        sa.UniqueConstraint("ioc_id", "threat_intel_id", name="uq_ioc_threat"),
    )
    op.create_index("ix_ioc_threat_ioc", "ioc_threat_intel", ["ioc_id"])
    op.create_index(
        "ix_ioc_threat_ti", "ioc_threat_intel", ["threat_intel_id"]
    )

    op.create_table(
        "ioc_malware",
        sa.Column(
            "ioc_id",
            uuid,
            sa.ForeignKey("indicators_of_compromise.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "malware_id",
            uuid,
            sa.ForeignKey("malware_metadata.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("role", sa.String(32), nullable=False, server_default="indicator"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.5"),
        sa.UniqueConstraint("ioc_id", "malware_id", name="uq_ioc_malware"),
    )
    op.create_index("ix_ioc_malware_ioc", "ioc_malware", ["ioc_id"])
    op.create_index("ix_ioc_malware_malware", "ioc_malware", ["malware_id"])

    # ----------------------------------------------------- NETWORK ASSETS
    op.create_table(
        "network_assets",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "device_id",
            uuid,
            sa.ForeignKey("devices.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("ip_address", inet, nullable=False),
        sa.Column("mac_address", mac),
        sa.Column("hostname", sa.String(255)),
        sa.Column("subnet", cidr),
        sa.Column("asn", sa.Integer),
        sa.Column("asn_org", sa.String(255)),
        sa.Column("country_code", sa.String(2)),
        sa.Column("city", sa.String(120)),
        sa.Column("latitude", sa.Float),
        sa.Column("longitude", sa.Float),
        sa.Column("is_external", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_tor_exit", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("reputation_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("since", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("tags", array_str, nullable=False, server_default="{}"),
        sa.Column("notes", sa.Text),
        sa.Column("extra", jsonb, nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "device_id", "ip_address", "since",
            name="uq_netasset_device_ip_since",
        ),
    )
    op.create_index("ix_netasset_ip", "network_assets", ["ip_address"])
    op.create_index("ix_netasset_asn", "network_assets", ["asn"])
    op.create_index("ix_netasset_country", "network_assets", ["country_code"])

    op.create_table(
        "network_asset_relationships",
        sa.Column("id", uuid, primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column(
            "src_asset_id",
            uuid,
            sa.ForeignKey("network_assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "dst_asset_id",
            uuid,
            sa.ForeignKey("network_assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("weight", sa.Integer, nullable=False, server_default="1"),
        sa.Column("first_observed", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed", sa.DateTime(timezone=True)),
        sa.Column("extra", jsonb, nullable=False, server_default="{}"),
        sa.UniqueConstraint(
            "src_asset_id", "dst_asset_id", "kind", name="uq_rel_src_dst_kind"
        ),
        sa.CheckConstraint("src_asset_id <> dst_asset_id", name="ck_rel_no_self_loop"),
    )
    op.create_index(
        "ix_rel_src", "network_asset_relationships", ["src_asset_id"]
    )
    op.create_index(
        "ix_rel_dst", "network_asset_relationships", ["dst_asset_id"]
    )
    op.create_index(
        "ix_rel_kind", "network_asset_relationships", ["kind"]
    )

    # ---------------------------------------------------------- REPORTS
    op.create_table(
        "reports",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("format", sa.String(8), nullable=False, server_default="pdf"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True)),
        sa.Column("artifact_uri", sa.String(1024)),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("error", sa.Text),
        sa.Column("parameters", jsonb, nullable=False, server_default="{}"),
        sa.Column("tags", array_str, nullable=False, server_default="{}"),
        sa.Column(
            "requested_by_user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('pending','running','completed','failed','expired')",
            name="ck_reports_status_enum",
        ),
    )
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_kind_generated", "reports", ["kind", "generated_at"])

    # ------------------------------------------------------- NOTIFICATIONS
    op.create_table(
        "notifications",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="3"),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text),
        sa.Column("extra", jsonb, nullable=False, server_default="{}"),
        sa.Column(
            "recipient_user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "alert_id",
            uuid,
            sa.ForeignKey("alerts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "report_id",
            uuid,
            sa.ForeignKey("reports.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "channel IN ('email','slack','webhook','pagerduty','sms','in_app')",
            name="ck_notif_channel_enum",
        ),
        sa.CheckConstraint(
            "status IN ('queued','sent','failed','cancelled','rate_limited')",
            name="ck_notif_status_enum",
        ),
    )
    op.create_index(
        "ix_notif_channel_status_ts",
        "notifications",
        ["channel", "status", "scheduled_at"],
    )
    op.create_index(
        "ix_notif_user_ts", "notifications", ["recipient_user_id", "scheduled_at"]
    )

    # -------------------------------------------------------- AUDIT LOGS
    op.create_table(
        "audit_logs",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64)),
        sa.Column("resource_id", sa.String(64)),
        sa.Column("outcome", sa.String(16), nullable=False, server_default="success"),
        sa.Column("source_ip", inet),
        sa.Column("user_agent", sa.String(512)),
        sa.Column("request_id", sa.String(64)),
        sa.Column("chain", sa.String(64)),
        sa.Column("before", jsonb, nullable=False, server_default="{}"),
        sa.Column("after", jsonb, nullable=False, server_default="{}"),
        sa.Column("reason", sa.Text),
        sa.CheckConstraint(
            "outcome IN ('success','failure','denied','error')",
            name="ck_audit_outcome_enum",
        ),
    )
    op.create_index("ix_audit_user_ts", "audit_logs", ["user_id", "ts"])
    op.create_index("ix_audit_action_ts", "audit_logs", ["action", "ts"])
    op.create_index(
        "ix_audit_resource", "audit_logs", ["resource_type", "resource_id"]
    )

    # ----------------------------------------------------------- SETTINGS
    op.create_table(
        "settings",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("scope", sa.String(16), nullable=False),
        sa.Column("scope_id", uuid),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value_json", jsonb, nullable=False),
        sa.Column(
            "value_type", sa.String(16), nullable=False, server_default="string"
        ),
        sa.Column("is_secret", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("description", sa.Text),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "updated_by_user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("scope", "scope_id", "key", name="uq_settings_scope_key"),
        sa.CheckConstraint(
            "scope IN ('global','user','honeypot','device','service')",
            name="ck_settings_scope_enum",
        ),
    )
    op.create_index("ix_settings_scope_key", "settings", ["scope", "key"])


def downgrade() -> None:
    # Drop in reverse FK dependency order.
    op.drop_index("ix_settings_scope_key", table_name="settings")
    op.drop_table("settings")

    op.drop_index("ix_audit_resource", table_name="audit_logs")
    op.drop_index("ix_audit_action_ts", table_name="audit_logs")
    op.drop_index("ix_audit_user_ts", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_notif_user_ts", table_name="notifications")
    op.drop_index("ix_notif_channel_status_ts", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_reports_kind_generated", table_name="reports")
    op.drop_index("ix_reports_status", table_name="reports")
    op.drop_table("reports")

    op.drop_index("ix_rel_kind", table_name="network_asset_relationships")
    op.drop_index("ix_rel_dst", table_name="network_asset_relationships")
    op.drop_index("ix_rel_src", table_name="network_asset_relationships")
    op.drop_table("network_asset_relationships")

    op.drop_index("ix_netasset_country", table_name="network_assets")
    op.drop_index("ix_netasset_asn", table_name="network_assets")
    op.drop_index("ix_netasset_ip", table_name="network_assets")
    op.drop_table("network_assets")

    op.drop_index("ix_ioc_malware_malware", table_name="ioc_malware")
    op.drop_index("ix_ioc_malware_ioc", table_name="ioc_malware")
    op.drop_table("ioc_malware")

    op.drop_index("ix_ioc_threat_ti", table_name="ioc_threat_intel")
    op.drop_index("ix_ioc_threat_ioc", table_name="ioc_threat_intel")
    op.drop_table("ioc_threat_intel")

    op.drop_index("ix_ioc_first_seen", table_name="indicators_of_compromise")
    op.drop_index("ix_ioc_value_inet", table_name="indicators_of_compromise")
    op.drop_index("ix_ioc_kind_value", table_name="indicators_of_compromise")
    op.drop_table("indicators_of_compromise")

    op.drop_index("ix_malware_type", table_name="malware_metadata")
    op.drop_index("ix_malware_family", table_name="malware_metadata")
    op.drop_table("malware_metadata")

    op.drop_index("ix_threat_tlp", table_name="threat_intelligence")
    op.drop_index("ix_threat_source_published", table_name="threat_intelligence")
    op.drop_table("threat_intelligence")

    op.drop_index("ix_logs_level_ts", table_name="logs")
    op.drop_index("ix_logs_source_ts", table_name="logs")
    op.drop_table("logs")

    op.drop_index("ix_events_severity_ts", table_name="events")
    op.drop_index("ix_events_kind_ts", table_name="events")
    op.drop_index("ix_events_source_ip_ts", table_name="events")
    op.drop_index("ix_events_ts", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_sessions_state", table_name="sessions")
    op.drop_index("ix_sessions_src_ip_started", table_name="sessions")
    op.drop_index("ix_sessions_honeypot_started", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index("ix_services_state", table_name="services")
    op.drop_index("ix_services_protocol", table_name="services")
    op.drop_table("services")

    op.drop_index("ix_devices_owner", table_name="devices")
    op.drop_index("ix_devices_kind", table_name="devices")
    op.drop_table("devices")

    op.drop_index("ix_role_permissions_permission", table_name="role_permissions")
    op.drop_index("ix_role_permissions_role", table_name="role_permissions")
    op.drop_table("role_permissions")

    op.drop_index("ix_user_roles_role", table_name="user_roles")
    op.drop_index("ix_user_roles_user", table_name="user_roles")
    op.drop_table("user_roles")

    op.drop_index("ix_permissions_resource", table_name="permissions")
    op.drop_index("ix_permissions_code", table_name="permissions")
    op.drop_table("permissions")

    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_table("roles")