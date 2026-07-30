# IoT Honeypot — PostgreSQL Schema Reference

This document is the authoritative reference for the PostgreSQL schema backing the IoT
honeypot platform. It covers **21 entities**, their columns, primary keys, foreign keys,
constraints, indexes, and a 3NF normalisation walkthrough.

Companion artefacts:

- **ER diagram:** [`erd.mmd`](./erd.mmd) (Mermaid `erDiagram`)
- **ORM models:** `backend/app/db/models/`
- **Migration:** `backend/alembic/versions/0002_extended_schema.py`
- **Previous migration:** `0001_initial.py` (created `users`, `honeypots`,
  `honeypot_events`, `alerts`, `ai_insights`)

---

## 1. Entity Inventory

| # | Table | Purpose | Source |
|---|---|---|---|
| 1 | `users` | Platform operators / API consumers | existing (0001) |
| 2 | `roles` | Named RBAC roles (e.g. `admin`, `analyst`) | new (0002) |
| 3 | `permissions` | Atomic (`resource`, `action`) capabilities | new (0002) |
| 4 | `user_roles` | M:N — users ↔ roles | new (0002) |
| 5 | `role_permissions` | M:N — roles ↔ permissions | new (0002) |
| 6 | `devices` | Physical / virtual device inventory | new (0002) |
| 7 | `services` | Listening services on a device or honeypot | new (0002) |
| 8 | `sessions` | Bounded attacker session (one row per session) | new (0002) |
| 9 | `events` | Normalised attacker-action ledger | new (0002) |
| 10 | `logs` | Raw, structured forensic logs | new (0002) |
| 11 | `threat_intelligence` | External intel feed items | new (0002) |
| 12 | `malware_metadata` | Malware family / sample reference data | new (0002) |
| 13 | `indicators_of_compromise` | Atomic observables (IPs, hashes, domains…) | new (0002) |
| 14 | `ioc_threat_intel` | M:N — IOCs ↔ threat intel reports | new (0002) |
| 15 | `ioc_malware` | M:N — IOCs ↔ malware families | new (0002) |
| 16 | `network_assets` | Observed IP/MAC positions + reputation | new (0002) |
| 17 | `network_asset_relationships` | Directed graph edges between network assets | new (0002) |
| 18 | `alerts` | Triaged incidents | existing (0001) |
| 19 | `ai_insights` | LLM-generated commentary cache | existing (0001) |
| 20 | `reports` | Generated analyst deliverables | new (0002) |
| 21 | `notifications` | Outbound channel messages | new (0002) |
| 22 | `audit_logs` | Append-only operator-action log | new (0002) |
| 23 | `settings` | Scoped key/value configuration | new (0002) |
| 24 | `honeypots` | Active honeypot deployments | existing (0001) |
| 25 | `honeypot_events` | Legacy event log (preserved) | existing (0001) |

The 16 entities requested by name map to: `users`, `roles`, `permissions`, `devices`,
`services`, `events`, `logs`, `sessions`, `alerts`, `reports`, `threat_intelligence`,
`malware_metadata`, `indicators_of_compromise`, `network_assets`, `audit_logs`,
`notifications`, `settings` (17 names — `roles` + `permissions` were specified
together as "Roles, Permissions" but each is its own table, plus `users` and the
existing `alerts` were listed).

---

## 2. Conventions

- **Primary keys:** all new tables use UUID v4 via `UUIDPKMixin`.
  This avoids leaking row counts and lets the API publish IDs without coordinating
  with a central sequence.
- **Timestamps:** every new table except `audit_logs` uses `TimestampMixin`
  (`created_at`, `updated_at` with `server_default=now()`). `audit_logs` uses a
  single explicit `ts` column because it is append-only and historical ingestion
  must preserve the original event time.
- **JSON payloads:** `metadata`, `context`, `extra`, `raw`, `parameters`,
  `structured`, `before`/`after` all use `JSONB` and default to `'{}'`. They are
  explicit opt-in extensions and are never indexed unless a path index is added
  via a partial GIN (out of scope for this migration).
- **Arrays:** `tags`, `mitre_tags`, `aliases`, `references` use
  `ARRAY(String(…))`. They are bounded by the column length and capped at the
  application layer.
- **Network types:** `INET` for IPv4/v6, `CIDR` for ranges, `MACADDR` for
  hardware addresses — leveraging PostgreSQL's native validators instead of
  `CHECK (ip ~ '^…$')` expressions.
- **Cascade rules:**
  - `CASCADE` when the child row is meaningless without the parent
    (e.g. `user_roles.user_id → users.id`).
  - `SET NULL` when the child should survive a parent deletion but lose the link
    (e.g. `events.session_id → sessions.id`).
- **Enum-style columns:** stored as `String(N)` with a `CHECK` constraint listing
  allowed values. This is preferred over a real `CREATE TYPE … AS ENUM` because
  adding a value to a real enum requires `ALTER TYPE … ADD VALUE` and a
  migration, while a CHECK constraint can be relaxed in-place.

---

## 3. 3NF Normalisation Walkthrough

### 3.1 First Normal Form (atomic values, no repeating groups)

- All scalar columns are atomic — no comma-separated `tag_list` strings.
- Repeating groups are moved into either a typed array column (when order doesn't
  matter and the group is bounded, e.g. `tags`, `mitre_tags`) or a child table
  (when relationships are independent, e.g. `user_roles`).
- The `indicators_of_compromise.value_*` columns are an *intentional* exception:
  IOCs are atomic observables of varying kinds (IP, CIDR, hash, domain…), so the
  polymorphic projection into sibling typed columns is 1NF-clean: each column
  holds one atomic value, and at most one of `value_inet`/`value_cidr`/`value_hash`/
  `value_domain`/`value_url`/`value_email`/`value_asn` is non-null per row (enforced
  by application logic). This is **not** a repeating group — it is a typed
  union implemented in columns rather than JSON.

### 3.2 Second Normal Form (no partial dependencies on a composite key)

- Every non-key column depends on the *whole* primary key. The M:N link tables
  (`user_roles`, `role_permissions`, `ioc_threat_intel`, `ioc_malware`,
  `network_asset_relationships`) have composite primary keys, and the only
  non-key columns they carry are descriptive provenance (`granted_at`,
  `confidence`, `observed_at`, `role`, `note`, edge metrics) — all of which
  describe the relationship itself, not one side of it. No column depends on
  only `user_id` without also depending on `role_id`.

### 3.3 Third Normal Form (no transitive dependencies)

- Every non-key column depends on the key, the whole key, and nothing but the key.
- **`users.full_name`** is stored as a single denormalised column rather than
  split into `first_name`/`last_name` because the latter would invite
  transitive dependencies (e.g. salutation rules) without operational benefit.
- **`devices.vendor` + `devices.model`** are kept separate even though a
  `devices.model_name` lookup table would be 3NF-cleaner — the cardinality is
  low (≈10s of vendors × 100s of models) and the join cost is not worth it. This
  is a *deliberate* deviation from BCNF, documented here so future reviewers
  don't "fix" it.
- **`threat_intelligence.source` + `threat_intelligence.external_id`** are kept
  inline (with `UNIQUE(source, external_id)`) rather than normalised into a
  `threat_sources` table, for the same reason: feeds are stable and few.
- **`network_assets`** does carry transitively-dependent facts: `asn` → `country`
  / `latitude` / `longitude` could be lifted into an `asn_registry` table, but
  these values are *point-in-time observations* from a particular lookup
  service (e.g. MaxMind) and may disagree across services. Pinning them to the
  asset snapshot is correct.

### 3.4 BCNF / domain-key normal form

- The schema is in BCNF for every table: every non-trivial functional dependency
  is implied by a candidate key.
- The only intentional denormalisations are the polymorphic IOC value columns
  and the `(source, external_id)` tuple on `threat_intelligence`, both
  justified above.

---

## 4. Per-Table Reference

### 4.1 `users` (existing, preserved)

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | `UUIDPKMixin` |
| `email` | `String(255) UNIQUE NOT NULL` | login identifier |
| `password_hash` | `String(255) NOT NULL` | bcrypt/argon2 hash |
| `full_name` | `String(120)` | display name |
| `is_active` | `Boolean NOT NULL DEFAULT true` | soft-disable |
| `is_superuser` | `Boolean NOT NULL DEFAULT false` | bypasses RBAC |
| `last_login_at` | `DateTime(timezone=True)` | |
| `created_at` | `DateTime(timezone=True) NOT NULL` | `TimestampMixin` |
| `updated_at` | `DateTime(timezone=True) NOT NULL` | `TimestampMixin` |

Referenced by: every ownership/actor FK in the new tables.

---

### 4.2 `roles`

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `name` | `String(64) UNIQUE NOT NULL` | e.g. `admin`, `analyst`, `viewer` |
| `description` | `String(255)` | human-readable |
| `is_system` | `Boolean NOT NULL DEFAULT false` | protected roles can't be deleted |
| `priority` | `Integer NOT NULL DEFAULT 0` | tie-break for "highest role wins" rules |
| `created_at` / `updated_at` | | |

Indexes: `ix_roles_name` (implicit via UNIQUE).
Referenced by: `user_roles`, `role_permissions`.

---

### 4.3 `permissions`

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `code` | `String(96) UNIQUE NOT NULL` | stable machine code, e.g. `alerts.write` |
| `resource` | `String(64) NOT NULL` | entity family (`alerts`, `devices`, …) |
| `action` | `String(32) NOT NULL` | verb (`read`, `write`, `delete`, `…`) |
| `description` | `Text` | |
| `created_at` / `updated_at` | | |

Indexes: `ix_permissions_code`, `ix_permissions_resource`.
The `(resource, action)` pair is the natural key; `code` is a flat string for
fast lookup. `UNIQUE(resource, action)` could replace `UNIQUE(code)` but the
code string is the value the API and middleware actually check.

---

### 4.4 `user_roles`

Composite-PK link table for `users` ↔ `roles`.

| Column | Type | Notes |
|---|---|---|
| `user_id` | `UUID PK, FK → users.id ON DELETE CASCADE` | |
| `role_id` | `UUID PK, FK → roles.id ON DELETE CASCADE` | |
| `granted_at` | `DateTime(timezone=True) NOT NULL DEFAULT now()` | audit trail |
| `granted_by` | `UUID FK → users.id ON DELETE SET NULL` | self-FK — who elevated |

Constraints: `UNIQUE(user_id, role_id)` (the PK already enforces this, but the
named UNIQUE constraint surfaces it in `pg_constraint`).
Indexes: `ix_user_roles_user`, `ix_user_roles_role` (PK already provides the
first).

---

### 4.5 `role_permissions`

Composite-PK link table for `roles` ↔ `permissions`. Pure mapping; no audit
columns because the audit log captures the change itself.

| Column | Type | Notes |
|---|---|---|
| `role_id` | `UUID PK, FK → roles.id ON DELETE CASCADE` | |
| `permission_id` | `UUID PK, FK → permissions.id ON DELETE CASCADE` | |

Indexes: `ix_role_permissions_role`, `ix_role_permissions_permission`.

---

### 4.6 `devices`

Asset inventory — physical or virtual IoT devices.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `name` | `String(120) NOT NULL` | friendly label |
| `vendor` | `String(80)` | e.g. `Hikvision`, `TP-Link` |
| `model` | `String(120)` | |
| `firmware_version` | `String(64)` | |
| `kind` | `String(40) NOT NULL` | `camera`, `router`, `printer`, `plc`, … |
| `mac_address` | `MACADDR UNIQUE` | one device per MAC |
| `primary_ip` | `INET` | current best-known IP |
| `tags` | `ARRAY(String(64)) NOT NULL DEFAULT '{}'` | free-form labels |
| `risk_score` | `Integer NOT NULL DEFAULT 0` | 0–100, composite signal |
| `is_active` | `Boolean NOT NULL DEFAULT true` | |
| `last_seen_at` | `String(40)` | free-form timestamp (snmp/agent text) |
| `metadata` | `JSONB NOT NULL DEFAULT '{}'` | |
| `owner_user_id` | `UUID FK → users.id ON DELETE SET NULL` | nullable so platform-level devices survive |
| `created_at` / `updated_at` | | |

Constraints:
- `UNIQUE(mac_address)` (`uq_devices_mac`)
- `CHECK (risk_score BETWEEN 0 AND 100)` (`ck_devices_risk_score_range`)

Indexes: `ix_devices_kind`, `ix_devices_owner`.

---

### 4.7 `services`

Listening services on a device or honeypot.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `device_id` | `UUID FK → devices.id ON DELETE CASCADE NULL` | device-bound |
| `honeypot_id` | `UUID FK → honeypots.id ON DELETE SET NULL NULL` | honeypot-realised |
| `name` | `String(120) NOT NULL` | e.g. `telnetd`, `http` |
| `protocol` | `String(16) NOT NULL` | `tcp`, `udp`, … |
| `port` | `Integer NOT NULL` | 0–65535 (validated at app layer) |
| `state` | `String(16) NOT NULL DEFAULT 'open'` | `open` / `filtered` / `closed` |
| `banner` | `String(255)` | grabbed banner text |
| `version` | `String(64)` | |
| `tls` | `Boolean NOT NULL DEFAULT false` | |
| `description` | `Text` | |
| `config` | `JSONB NOT NULL DEFAULT '{}'` | service-specific config |
| `created_at` / `updated_at` | | |

Constraints: `UNIQUE(device_id, protocol, port)` (`uq_services_device_proto_port`)
prevents duplicate listeners on the same device.
Indexes: `ix_services_state`, `ix_services_protocol`.

---

### 4.8 `sessions`

A bounded attacker session. One row per (source IP, honeypot, protocol) window.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `started_at` | `DateTime(timezone=True) NOT NULL` | |
| `ended_at` | `DateTime(timezone=True)` | NULL while open |
| `state` | `String(16) NOT NULL DEFAULT 'open'` | `open` / `closed` / `timeout` |
| `src_ip` | `INET` | attacker |
| `src_port` | `Integer` | |
| `protocol` | `String(16) NOT NULL` | |
| `user_agent` | `String(512)` | |
| `bytes_in` / `bytes_out` | `BigInteger NOT NULL DEFAULT 0` | |
| `commands_count` | `Integer NOT NULL DEFAULT 0` | |
| `authenticated` | `Boolean NOT NULL DEFAULT false` | |
| `mitre_tags` | `ARRAY(String(80)) NOT NULL DEFAULT '{}'` | ATT&CK technique IDs |
| `device_id` | `UUID FK → devices.id ON DELETE SET NULL` | |
| `honeypot_id` | `UUID FK → honeypots.id ON DELETE CASCADE` | sessions die with honeypot |
| `created_at` / `updated_at` | | |

Constraints: `CHECK (ended_at IS NULL OR ended_at >= started_at)`
(`ck_sessions_ended_after_started`).
Indexes: `ix_sessions_honeypot_started`, `ix_sessions_src_ip_started`,
`ix_sessions_state`.

---

### 4.9 `events`

The normalised attacker-action ledger — append-only.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `ts` | `DateTime(timezone=True) NOT NULL DEFAULT now()` | source-of-truth time |
| `kind` | `String(40) NOT NULL` | `login`, `cmd`, `exec`, `http`, `rtsp`, `mqtt`, `modbus`, … |
| `severity` | `Integer NOT NULL` | 1–5 |
| `protocol` | `String(16)` | |
| `src_ip` / `src_port` | `INET` / `Integer` | |
| `dst_ip` / `dst_port` | `INET` / `Integer` | |
| `user_agent` | `String(512)` | |
| `username` | `String(120)` | captured login |
| `password` | `String(255)` | captured password (consider hashing at app layer) |
| `command` | `Text` | shell / protocol command |
| `payload_size` | `BigInteger NOT NULL DEFAULT 0` | |
| `mitre_tags` | `ARRAY(String(80)) NOT NULL DEFAULT '{}'` | |
| `success` | `Boolean` | |
| `confidence` | `Float NOT NULL DEFAULT 1.0` | 0.0–1.0 |
| `extra` | `JSONB NOT NULL DEFAULT '{}'` | protocol-specific extras |
| `device_id` | `UUID FK → devices.id ON DELETE SET NULL` | |
| `service_id` | `UUID FK → services.id ON DELETE SET NULL` | |
| `honeypot_id` | `UUID FK → honeypots.id ON DELETE SET NULL` | |
| `session_id` | `UUID FK → sessions.id ON DELETE SET NULL` | |
| `log_id` | `UUID FK → logs.id ON DELETE SET NULL` | back-pointer to raw log |
| `created_at` / `updated_at` | | |

Constraints: `CHECK (severity BETWEEN 1 AND 5)` (`ck_events_severity_range`).
Indexes: `ix_events_ts`, `ix_events_source_ip_ts`, `ix_events_kind_ts`,
`ix_events_severity_ts`. Designed to be promoted to a **TimescaleDB
hypertable** on `ts` later.

---

### 4.10 `logs`

Raw forensic logs — the unstructured complement to `events`.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `ts` | `DateTime(timezone=True) NOT NULL DEFAULT now()` | |
| `source` | `String(64) NOT NULL` | `cowrie`, `dionaea`, `syslog`, … |
| `level` | `String(16) NOT NULL DEFAULT 'info'` | `debug`/`info`/`warn`/`error` |
| `message` | `Text NOT NULL` | human-readable line |
| `structured` | `JSONB NOT NULL DEFAULT '{}'` | parsed fields |
| `device_id` | `UUID FK → devices.id ON DELETE SET NULL` | |
| `honeypot_id` | `UUID FK → honeypots.id ON DELETE SET NULL` | |
| `event_id` | `UUID FK → events.id ON DELETE SET NULL` | optional normalisation pointer |
| `created_at` / `updated_at` | | |

Indexes: `ix_logs_source_ts`, `ix_logs_level_ts`.

---

### 4.11 `threat_intelligence`

External intel-feed items (one row per feed entry).

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `source` | `String(64) NOT NULL` | feed name (`mitre`, `otx`, …) |
| `external_id` | `String(255) NOT NULL` | feed-native ID |
| `title` | `String(255) NOT NULL` | |
| `description` | `Text` | |
| `published_at` | `DateTime(timezone=True)` | |
| `tlp` | `String(16) NOT NULL DEFAULT 'amber'` | TLP marking |
| `confidence` | `Integer NOT NULL DEFAULT 50` | 0–100 |
| `severity` | `String(16)` | |
| `mitre_tags` | `ARRAY(String(80)) NOT NULL DEFAULT '{}'` | |
| `references` | `ARRAY(String(512)) NOT NULL DEFAULT '{}'` | URLs |
| `raw` | `JSONB NOT NULL DEFAULT '{}'` | original payload |
| `created_at` / `updated_at` | | |

Constraints:
- `UNIQUE(source, external_id)` (`uq_threat_source_extid`)
- `CHECK (tlp IN ('white','green','amber','amber+strict','red'))`
  (`ck_threat_tlp_enum`)

Indexes: `ix_threat_source_published`, `ix_threat_tlp`.

---

### 4.12 `malware_metadata`

Malware family / sample reference data.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `sha256` | `String(64) UNIQUE NOT NULL` | primary sample hash |
| `sha1` | `String(40)` | |
| `md5` | `String(32)` | |
| `family` | `String(120)` | e.g. `Mirai`, `Mozi` |
| `malware_type` | `String(32) NOT NULL DEFAULT 'other'` | enum-checked |
| `aliases` | `ARRAY(String(120)) NOT NULL DEFAULT '{}'` | |
| `first_seen_at` / `last_seen_at` | `DateTime(timezone=True)` | |
| `tlp` | `String(16)` | TLP marking |
| `description` | `Text` | |
| `raw` | `JSONB NOT NULL DEFAULT '{}'` | |
| `created_at` / `updated_at` | | |

Constraints:
- `UNIQUE(sha256)` (`uq_malware_sha256`)
- `CHECK (malware_type IN ('ransomware','trojan','worm','botnet','rootkit',
  'spyware','downloader','dropper','backdoor','exploit','other'))`
  (`ck_malware_type_enum`)

Indexes: `ix_malware_family`, `ix_malware_type`.

---

### 4.13 `indicators_of_compromise`

Atomic observables — the spine of intel correlation.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `kind` | `String(16) NOT NULL` | `ip`, `domain`, `url`, `sha256`, `email`, `cidr`, `asn` |
| `value_inet` | `INET` | populated for `kind='ip'` |
| `value_cidr` | `CIDR` | populated for `kind='cidr'` |
| `value_hash` | `String(128)` | populated for `kind='sha256'` |
| `value_domain` | `String(255)` | |
| `value_url` | `String(2048)` | |
| `value_email` | `String(255)` | |
| `value_asn` | `Integer` | populated for `kind='asn'` |
| `source` | `String(64) NOT NULL` | who reported it |
| `confidence` | `Integer NOT NULL DEFAULT 50` | |
| `first_seen_at` | `DateTime(timezone=True)` | |
| `last_seen_at` | `DateTime(timezone=True)` | |
| `expires_at` | `DateTime(timezone=True)` | TTL for ephemeral indicators |
| `context` | `JSONB NOT NULL DEFAULT '{}'` | |
| `description` | `Text` | |
| `created_at` / `updated_at` | | |

Constraints:
- `CHECK (kind IN ('ip','domain','url','sha256','email','cidr','asn'))`
  (`ck_ioc_kind_enum`)
- `UNIQUE(kind, value_inet, source)` / `UNIQUE(kind, value_cidr, source)` /
  `UNIQUE(kind, value_hash, source)` / `UNIQUE(kind, value_domain, source)` /
  `UNIQUE(kind, value_url, source)` / `UNIQUE(kind, value_email, source)` /
  `UNIQUE(kind, value_asn, source)` (seven named constraints, each restricted
  to the relevant column).

Indexes: `ix_ioc_kind`, `ix_ioc_source`, `ix_ioc_expires`.
Note: PostgreSQL doesn't permit a partial UNIQUE on `kind='ip'` without
specific syntax; instead seven full UNIQUE constraints are declared and the
application layer guarantees only one value-column is non-null per row.

---

### 4.14 `ioc_threat_intel`

M:N link: IOC ↔ threat-intelligence report.

| Column | Type | Notes |
|---|---|---|
| `ioc_id` | `UUID PK, FK → indicators_of_compromise.id ON DELETE CASCADE` | |
| `threat_intel_id` | `UUID PK, FK → threat_intelligence.id ON DELETE CASCADE` | |
| `confidence` | `Float` | per-relationship confidence |
| `observed_at` | `DateTime(timezone=True)` | when the IOC was seen in that report |
| `note` | `Text` | |

---

### 4.15 `ioc_malware`

M:N link: IOC ↔ malware family.

| Column | Type | Notes |
|---|---|---|
| `ioc_id` | `UUID PK, FK → indicators_of_compromise.id ON DELETE CASCADE` | |
| `malware_id` | `UUID PK, FK → malware_metadata.id ON DELETE CASCADE` | |
| `role` | `String(32) NOT NULL DEFAULT 'indicator'` | `dropper`/`downloader`/`payload`/`exfil`/`c2`/`indicator` |
| `note` | `Text` | |

---

### 4.16 `network_assets`

Observed network position of a device, versioned over time.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `device_id` | `UUID FK → devices.id ON DELETE CASCADE` | |
| `ip_address` | `INET NOT NULL` | |
| `subnet` | `CIDR` | |
| `mac_address` | `MACADDR` | |
| `hostname` | `String(255)` | |
| `asn` | `String(32)` | |
| `country` | `String(64)` | |
| `latitude` / `longitude` | `Float` | geo coords |
| `reputation_score` | `Float NOT NULL DEFAULT 0.0` | |
| `is_internal` | `Boolean NOT NULL DEFAULT false` | |
| `since` | `DateTime(timezone=True) NOT NULL` | observation start |
| `until` | `DateTime(timezone=True)` | observation end (NULL = current) |
| `metadata` | `JSONB NOT NULL DEFAULT '{}'` | |
| `created_at` / `updated_at` | | |

Constraints:
- `UNIQUE(device_id, ip_address, since)` (`uq_network_assets_device_ip_since`)
  — one snapshot per (device, IP, since-time). New snapshots close the previous
  one by setting `until`.

Indexes: `ix_network_assets_ip`, `ix_network_assets_device`.

---

### 4.17 `network_asset_relationships`

Directed edges in the network graph.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `source_id` | `UUID FK → network_assets.id ON DELETE CASCADE` | |
| `destination_id` | `UUID FK → network_assets.id ON DELETE CASCADE` | |
| `edge_type` | `String(32) NOT NULL` | `connects_to`/`routes_to`/`resolves_to` |
| `protocol` | `String(16)` | |
| `port` | `Integer` | |
| `packet_count` | `Integer NOT NULL DEFAULT 0` | |
| `bytes` | `BigInteger NOT NULL DEFAULT 0` | |
| `first_seen_at` / `last_seen_at` | `DateTime(timezone=True)` | |
| `metadata` | `JSONB NOT NULL DEFAULT '{}'` | |

Constraints: `CHECK (source_id <> destination_id)`
(`ck_network_rel_no_self_loop`).
Indexes: `ix_network_rel_src`, `ix_network_rel_dst`, `ix_network_rel_type`.

---

### 4.18 `alerts` (existing, preserved)

Triaged incidents. Referenced by `notifications.alert_id`.

---

### 4.19 `ai_insights` (existing, preserved)

LLM-generated commentary cache. Standalone.

---

### 4.20 `reports`

Generated analyst deliverables.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `title` | `String(255) NOT NULL` | |
| `report_type` | `String(32) NOT NULL` | `executive`/`technical`/`threat`/`incident`/`ioc` |
| `status` | `String(16) NOT NULL DEFAULT 'pending'` | `pending`/`running`/`completed`/`failed`/`expired` |
| `period_start` / `period_end` | `DateTime(timezone=True)` | reporting window |
| `artifact_uri` | `String(1024)` | S3 / filesystem reference |
| `artifact_format` | `String(16)` | `pdf`/`html`/`json`/`csv` |
| `artifact_size` | `BigInteger` | bytes |
| `parameters` | `JSONB NOT NULL DEFAULT '{}'` | inputs to the generator |
| `error` | `Text` | failure detail |
| `tags` | `ARRAY(String(64)) NOT NULL DEFAULT '{}'` | |
| `requested_by_user_id` | `UUID FK → users.id ON DELETE SET NULL` | |
| `generated_at` | `DateTime(timezone=True)` | |
| `expires_at` | `DateTime(timezone=True)` | |
| `created_at` / `updated_at` | | |

Constraints:
- `CHECK (status IN ('pending','running','completed','failed','expired'))`
  (`ck_reports_status_enum`)
- `CHECK (report_type IN ('executive','technical','threat','incident','ioc'))`
  (`ck_reports_type_enum`)

Indexes: `ix_reports_status`, `ix_reports_type`, `ix_reports_requested_by`,
`ix_reports_period`.

---

### 4.21 `notifications`

Outbound channel messages.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `channel` | `String(16) NOT NULL` | `email`/`slack`/`webhook`/`pagerduty`/`sms`/`in_app` |
| `status` | `String(16) NOT NULL DEFAULT 'queued'` | `queued`/`sending`/`sent`/`failed`/`rate_limited` |
| `subject` | `String(255)` | |
| `body` | `Text` | rendered message |
| `destination` | `String(255)` | email / webhook URL / phone |
| `severity` | `String(16)` | |
| `attempts` | `Integer NOT NULL DEFAULT 0` | retry counter |
| `last_error` | `Text` | |
| `last_attempt_at` | `DateTime(timezone=True)` | |
| `scheduled_at` | `DateTime(timezone=True)` | |
| `sent_at` | `DateTime(timezone=True)` | |
| `alert_id` | `UUID FK → alerts.id ON DELETE SET NULL` | optional alert trigger |
| `report_id` | `UUID FK → reports.id ON DELETE SET NULL` | optional report trigger |
| `recipient_user_id` | `UUID FK → users.id ON DELETE SET NULL` | in-app target |
| `created_at` / `updated_at` | | |

Constraints:
- `CHECK (channel IN ('email','slack','webhook','pagerduty','sms','in_app'))`
- `CHECK (status IN ('queued','sending','sent','failed','rate_limited'))`

Indexes: `ix_notifications_status`, `ix_notifications_channel`,
`ix_notifications_recipient`.

---

### 4.22 `audit_logs`

Append-only operator-action log. The single source of truth for "who did what
when". Uses a self-managed `ts` column (no `TimestampMixin`) because historical
imports must preserve the original event time.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `ts` | `DateTime(timezone=True) NOT NULL DEFAULT now()` | |
| `actor_user_id` | `UUID FK → users.id ON DELETE SET NULL` | |
| `actor_ip` | `INET` | |
| `action` | `String(64) NOT NULL` | verb (`create`, `update`, `delete`, `login`, …) |
| `resource_type` | `String(64)` | target entity family |
| `resource_id` | `UUID` | target row |
| `outcome` | `String(16) NOT NULL` | `success`/`denied`/`error` |
| `request_id` | `String(64)` | chains related actions |
| `before` | `Text` | JSON-encoded pre-state |
| `after` | `Text` | JSON-encoded post-state |
| `context` | `JSONB NOT NULL DEFAULT '{}'` | additional metadata |

Constraints: `CHECK (outcome IN ('success','denied','error'))`.
Indexes: `ix_audit_ts`, `ix_audit_actor`, `ix_audit_action`,
`ix_audit_resource`.

---

### 4.23 `settings`

Scoped key/value configuration with fallback hierarchy
(`global` → `user`/`honeypot`/`device`/`service`).

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `scope` | `String(16) NOT NULL` | `global`/`user`/`honeypot`/`device`/`service` |
| `scope_id` | `UUID` | polymorphic FK target (not enforced) |
| `key` | `String(128) NOT NULL` | |
| `value` | `Text` | raw value (parsed via `value_type`) |
| `value_type` | `String(16) NOT NULL DEFAULT 'string'` | `string`/`int`/`float`/`bool`/`json` |
| `is_secret` | `Boolean NOT NULL DEFAULT false` | UI/API redacts this value |
| `version` | `Integer NOT NULL DEFAULT 1` | optimistic concurrency |
| `description` | `Text` | |
| `updated_by_user_id` | `UUID FK → users.id ON DELETE SET NULL` | |
| `created_at` / `updated_at` | | |

Constraints:
- `UNIQUE(scope, scope_id, key)` (`uq_settings_scope_scopeid_key`)
- `CHECK (scope IN ('global','user','honeypot','device','service'))`
- `CHECK (value_type IN ('string','int','float','bool','json'))`

Indexes: `ix_settings_scope_key`, `ix_settings_scope_scopeid`.

---

## 5. Index Catalogue

| Table | Index | Columns | Rationale |
|---|---|---|---|
| `roles` | (UNIQUE) | `name` | natural-key lookup |
| `permissions` | `ix_permissions_code` | `code` | permission checks |
| `permissions` | `ix_permissions_resource` | `resource` | permission grouping |
| `user_roles` | (PK) | `(user_id, role_id)` | join performance |
| `user_roles` | `ix_user_roles_user` | `user_id` | reverse lookup |
| `user_roles` | `ix_user_roles_role` | `role_id` | role expansion |
| `role_permissions` | (PK) | `(role_id, permission_id)` | |
| `role_permissions` | `ix_role_permissions_role` | `role_id` | |
| `role_permissions` | `ix_role_permissions_permission` | `permission_id` | |
| `devices` | `ix_devices_kind` | `kind` | filter by type |
| `devices` | `ix_devices_owner` | `owner_user_id` | per-user inventory |
| `services` | `ix_services_state` | `state` | filter open ports |
| `services` | `ix_services_protocol` | `protocol` | |
| `sessions` | `ix_sessions_honeypot_started` | `(honeypot_id, started_at)` | time-series per honeypot |
| `sessions` | `ix_sessions_src_ip_started` | `(src_ip, started_at)` | attacker history |
| `sessions` | `ix_sessions_state` | `state` | open session queries |
| `events` | `ix_events_ts` | `ts` | BRIN/hypertable candidate |
| `events` | `ix_events_source_ip_ts` | `(src_ip, ts)` | attacker time-series |
| `events` | `ix_events_kind_ts` | `(kind, ts)` | per-protocol time-series |
| `events` | `ix_events_severity_ts` | `(severity, ts)` | severity dashboards |
| `logs` | `ix_logs_source_ts` | `(source, ts)` | per-source time-series |
| `logs` | `ix_logs_level_ts` | `(level, ts)` | error dashboards |
| `threat_intelligence` | (UNIQUE) | `(source, external_id)` | dedup |
| `threat_intelligence` | `ix_threat_source_published` | `(source, published_at)` | feed slicing |
| `threat_intelligence` | `ix_threat_tlp` | `tlp` | TLP filtering |
| `malware_metadata` | (UNIQUE) | `sha256` | sample lookup |
| `malware_metadata` | `ix_malware_family` | `family` | family browse |
| `malware_metadata` | `ix_malware_type` | `malware_type` | type filter |
| `indicators_of_compromise` | (UNIQUE ×7) | `(kind, value_*, source)` | dedup |
| `indicators_of_compromise` | `ix_ioc_kind` | `kind` | |
| `indicators_of_compromise` | `ix_ioc_source` | `source` | |
| `indicators_of_compromise` | `ix_ioc_expires` | `expires_at` | TTL eviction |
| `network_assets` | (UNIQUE) | `(device_id, ip_address, since)` | snapshot dedup |
| `network_assets` | `ix_network_assets_ip` | `ip_address` | |
| `network_assets` | `ix_network_assets_device` | `device_id` | |
| `network_asset_relationships` | `ix_network_rel_src` | `source_id` | outgoing edges |
| `network_asset_relationships` | `ix_network_rel_dst` | `destination_id` | incoming edges |
| `network_asset_relationships` | `ix_network_rel_type` | `edge_type` | |
| `reports` | `ix_reports_status` | `status` | |
| `reports` | `ix_reports_type` | `report_type` | |
| `reports` | `ix_reports_requested_by` | `requested_by_user_id` | |
| `reports` | `ix_reports_period` | `(period_start, period_end)` | |
| `notifications` | `ix_notifications_status` | `status` | retry queue |
| `notifications` | `ix_notifications_channel` | `channel` | |
| `notifications` | `ix_notifications_recipient` | `recipient_user_id` | per-user inbox |
| `audit_logs` | `ix_audit_ts` | `ts` | time-range queries |
| `audit_logs` | `ix_audit_actor` | `actor_user_id` | per-user audit |
| `audit_logs` | `ix_audit_action` | `action` | |
| `audit_logs` | `ix_audit_resource` | `(resource_type, resource_id)` | target history |
| `settings` | (UNIQUE) | `(scope, scope_id, key)` | dedup |
| `settings` | `ix_settings_scope_key` | `(scope, key)` | |
| `settings` | `ix_settings_scope_scopeid` | `(scope, scope_id)` | |

---

## 6. Constraint Catalogue

| Table | Constraint | Expression |
|---|---|---|
| `devices` | `uq_devices_mac` | `UNIQUE (mac_address)` |
| `devices` | `ck_devices_risk_score_range` | `risk_score BETWEEN 0 AND 100` |
| `services` | `uq_services_device_proto_port` | `UNIQUE (device_id, protocol, port)` |
| `sessions` | `ck_sessions_ended_after_started` | `ended_at IS NULL OR ended_at >= started_at` |
| `events` | `ck_events_severity_range` | `severity BETWEEN 1 AND 5` |
| `threat_intelligence` | `uq_threat_source_extid` | `UNIQUE (source, external_id)` |
| `threat_intelligence` | `ck_threat_tlp_enum` | `tlp IN ('white','green','amber','amber+strict','red')` |
| `malware_metadata` | `uq_malware_sha256` | `UNIQUE (sha256)` |
| `malware_metadata` | `ck_malware_type_enum` | `malware_type IN (…)` |
| `indicators_of_compromise` | `ck_ioc_kind_enum` | `kind IN ('ip','domain','url','sha256','email','cidr','asn')` |
| `indicators_of_compromise` | 7 × `UNIQUE(kind, value_*, source)` | polymorphic dedup |
| `network_assets` | `uq_network_assets_device_ip_since` | `UNIQUE (device_id, ip_address, since)` |
| `network_asset_relationships` | `ck_network_rel_no_self_loop` | `source_id <> destination_id` |
| `reports` | `ck_reports_status_enum` | `status IN ('pending','running','completed','failed','expired')` |
| `reports` | `ck_reports_type_enum` | `report_type IN ('executive','technical','threat','incident','ioc')` |
| `notifications` | (channel enum) | `channel IN ('email','slack','webhook','pagerduty','sms','in_app')` |
| `notifications` | (status enum) | `status IN ('queued','sending','sent','failed','rate_limited')` |
| `audit_logs` | (outcome enum) | `outcome IN ('success','denied','error')` |
| `settings` | `uq_settings_scope_scopeid_key` | `UNIQUE (scope, scope_id, key)` |
| `settings` | (scope enum) | `scope IN ('global','user','honeypot','device','service')` |
| `settings` | (value_type enum) | `value_type IN ('string','int','float','bool','json')` |

---

## 7. Relationships

| From | Cardinality | To | Notes |
|---|---|---|---|
| `users` 1—* `user_roles` *—1 `roles` | M:N | link with `granted_by` self-FK | |
| `roles` 1—* `role_permissions` *—1 `permissions` | M:N | | |
| `users` 1—* `devices` | 1:N | `owner_user_id` SET NULL | |
| `devices` 1—* `services` | 1:N | `device_id` CASCADE | |
| `honeypots` 1—* `services` | 1:N | `honeypot_id` SET NULL | |
| `devices` 1—* `sessions` | 1:N | `device_id` SET NULL | |
| `honeypots` 1—* `sessions` | 1:N | `honeypot_id` CASCADE | |
| `sessions` 1—* `events` | 1:N | `session_id` SET NULL | |
| `services` 1—* `events` | 1:N | `service_id` SET NULL | |
| `events` 1—* `logs` | 1:N | `event_id` SET NULL | optional back-link |
| `indicators_of_compromise` *—* `threat_intelligence` | M:N | `ioc_threat_intel` | |
| `indicators_of_compromise` *—* `malware_metadata` | M:N | `ioc_malware` | |
| `devices` 1—* `network_assets` | 1:N | `device_id` CASCADE | time-versioned snapshots |
| `network_assets` *—* `network_assets` | M:N self | `network_asset_relationships` | directed graph |
| `users` 1—* `reports` | 1:N | `requested_by_user_id` SET NULL | |
| `alerts` 1—* `notifications` | 1:N | `alert_id` SET NULL | |
| `reports` 1—* `notifications` | 1:N | `report_id` SET NULL | |
| `users` 1—* `notifications` | 1:N | `recipient_user_id` SET NULL | in-app inbox |
| `users` 1—* `audit_logs` | 1:N | `actor_user_id` SET NULL | |
| `users` 1—* `settings` | 1:N | `updated_by_user_id` SET NULL | scoped config |

---

## 8. Migration Notes

- Apply with: `alembic upgrade head` from `backend/`.
- Downgrade is the exact reverse of upgrade — every table is dropped after its
  dependents.
- Both `events` and `notifications` reference the existing `alerts` table; that
  dependency is satisfied by `0001_initial.py`.
- `sessions` is created **before** `events` because `events.session_id` FKs it.
- `events` is created **before** `logs` because `logs.event_id` FKs it.
- `events` and `logs` are both nullable-FK targets from `network_asset_relationships.metadata`
  — wait, no, those are JSONB, not FKs. The FK chain is:
  `roles`/`permissions` → `user_roles`/`role_permissions` →
  `devices`/`services` → `sessions` → `events` → `logs`, plus
  `threat_intelligence`/`malware_metadata` → IOCs → links.
- The `events` table is designed to be promoted to a **TimescaleDB hypertable**
  on `ts` later via `SELECT create_hypertable('events','ts')`.