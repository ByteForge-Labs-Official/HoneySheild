# Data Model (PostgreSQL)

Drawn with SQLAlchemy 2.x.  All attacker-derived strings are bounded to ≤4 KiB
before persistence (`ingest_normalizer.normalize_string`).

```
devices          sessions        attacks          events           iocs
─────────        ────────        ────────         ───────          ────
id (uuid)        id (uuid)       id (uuid)        id (uuid)        id (uuid)
type             device_id →     session_id →     attack_id →      value
vendor           remote_ip       started_at       ts               type (ip|domain|hash|...)
model            started_at      ended_at         kind (login|cmd|exec|http|rtsp|mqtt|modbus|...)
firmware_ver     ended_at        protocol         severity
bait_ports[]     bytes_in/out    success (bool)   payload (jsonb)
created_at       commands[]      payload (jsonb)  src_ip
                                src_ip           dst_ip
                                dst_port
                                user_agent
                                mitre_tags[]
```

## Key relations

* `attack.mitre_tags` is a `text[]` populated by the AI service.  We cap it at
  32 tags and at most 80 chars per tag.
* `event` is a normalized append-only stream; it is the single source of truth
  for `attacks` analytics.  The `attacks` row is the **session-level summary**,
  the `events` are the **action-level ledger**.
* `iocs` is an extracted table populated by both rules-based and AI-based
  pipelines; it's queryable from Grafana and the dashboard.

## Time-series strategy

* One PostgreSQL table per "rolling" metric, with a `BRIN (ts)` index.
* Materialized views (`mv_attacks_per_min`, `mv_top_offenders`) feed Grafana
  without needing a separate TSDB.

## Retention

| Tier | Default retention | Mechanism |
|---|---|---|
| Hot (Postgres) | 30 days | cron `pg_partman` |
| Warm (Elasticsearch) | 90 days | ILM policy |
| Cold (filesystem `data/`) | indefinite | manual pruning |
