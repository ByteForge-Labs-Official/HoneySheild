# 📈 Monitoring System

End-to-end observability for the IoT Honeynet Research Platform: **host**,
**container**, **application**, **database**, and **API** metrics scraped by
Prometheus and visualised by Grafana. Alertmanager fires when thresholds
are breached; blackbox-exporter continuously probes critical endpoints.

```
                       ┌─────────────────────────┐
                       │     Grafana (3000)      │
                       │ dashboards + alerts     │
                       └────────────▲────────────┘
                                    │ PromQL
                       ┌────────────┴────────────┐
                       │   Prometheus (9090)     │
                       │  scrape + evaluate +    │
                       │  Alertmanager rule link │
                       └─▲─────▲─────▲─────▲─────┘
            ┌───────────┘     │     │     │
            │         ┌───────┘     │     └───────────┐
            │         │       ┌─────┘                 │
   ┌────────┴───┐ ┌───┴────┐  ┌─┴─────────┐  ┌────────┴────────┐
   │ honeynet-  │ │ cAdvi- │  │ postgres- │  │  redis-         │
   │ api :8000  │ │  sor   │  │ exporter  │  │  exporter       │
   │ /metrics   │ │ :8080  │  │ :9187     │  │  :9121          │
   └────────────┘ └────────┘  └───────────┘  └─────────────────┘
            ▲             ▲
            │             │
       node-exporter    honeypots / IDS / etc.
       :9100
            ▲
            └── blackbox :9115 probes external endpoints
```

---

## 🎯 Why monitoring matters here

| Reason | What we get |
|---|---|
| **Triage** | Spot a breach in the gateway container before it spreads. |
| **Capacity** | Know when to add a honeypot replica or DB read-replica. |
| **SLOs** | Track 99th-percentile ingest latency and feed real numbers into runbooks. |
| **Compliance** | Provide "system was healthy at 03:14:22 UTC" evidence after an incident. |
| **Detection** | A spike in `honeypot_unauth_attempts_total` *itself* is a finding. |

A honeypot platform can't treat observability as an afterthought — losing
visibility = losing the entire dataset.

---

## 🧱 Inventory of exporters

| Exporter | Port | Scrapes | Required |
|---|---|---|---|
| `node-exporter` | 9100 | Host CPU / memory / disk / network / processes | ✅ |
| `cadvisor` | 8080 | Per-container resource usage, OOM events | ✅ |
| `postgres-exporter` | 9187 | Postgres connection pools, replication, locks, I/O | ✅ |
| `redis-exporter` | 9121 | Redis memory, evictions, hit-rate, pub/sub lag | ✅ |
| `blackbox-exporter` | 9115 | HTTP/TCP/ICMP synthetic probes | ✅ |
| honeynet-api `/metrics` | 8000 | App + API + DB pool metrics via `prometheus-fastapi-instrumentator` | ✅ |
| Celery `celery-exporter` | 9808 | Active / reserved / failed tasks | opt |
| Suricata exporter | 9915 | Suricata drop / flow / alert counters | opt |
| Zeek exporter | 9916 | Zeek connection / notice counters | opt |

---

## 📚 Every metric, explained

Metrics are grouped into **six** tiers. Each card lists the canonical
Prometheus exposition name, type, and what to do with it.

### 1️⃣ Host — CPU

| Metric | Type | Origin | Description |
|---|---|---|---|
| `node_cpu_seconds_total{mode}` | counter | node-exporter | Cumulative CPU time, broken down by `mode` (`user`, `system`, `idle`, `iowait`, `steal`, `nice`, `irq`, `softirq`). Multiply by `100 / count(by(cpu, mode))` to get utilisation %. |
| `node_load1 / node_load5 / node_load15` | gauge | node-exporter | 1/5/15-min exponentially-weighted run-queue length. Alert when `> 2 × ncpu`. |
| `node_cpu_core_throttles_total` | counter | node-exporter | Total number of periods a CPU was throttled by cgroup. A persistent positive rate means the container is being capped — raise its limit. |
| `rate(node_cpu_seconds_total{mode!="idle"}[5m])` | derived | PromQL | Per-host CPU utilisation over the last 5 minutes. Alert > 80 %. |
| `honeynet_cpu_usage_percent{service}` | gauge | cadvisor | Same as above, but per-container. Critical for spotting a single honeypot on a busy node. |

### 2️⃣ Host — Memory

| Metric | Type | Description |
|---|---|---|
| `node_memory_MemTotal_bytes` | gauge | Total physical RAM on host. Constant; used as denominator. |
| `node_memory_MemAvailable_bytes` | gauge | RAM available for new workloads. Alert when < 15 % of total. |
| `node_memory_Buffers_bytes`, `node_memory_Cached_bytes` | gauge | Kernel page cache — cheap, free-able. |
| `node_memory_SwapTotal_bytes`, `node_memory_Swap_free_bytes` | gauge | Swap usage. Any non-zero `node_vmstat_pswpin` is a red flag — swap on a honeypot host slows IDS capture. |
| `node_vmstat_pgpgin / pgpgout` | counter | Page-in / page-out rate. Sustained activity ⇒ memory pressure. |
| `container_memory_rss{name=…}` | gauge | RSS per container; alarm on RSS climbing while cache is empty (likely leak). |
| `container_memory_failures_total{name, type}` | counter | `type=oom` is critical. |

### 3️⃣ Host — Disk

| Metric | Type | Description |
|---|---|---|
| `node_filesystem_size_bytes{mountpoint}` | gauge | Total bytes per mountpoint. |
| `node_filesystem_avail_bytes{mountpoint}` | gauge | Bytes free. Alert when < 15 % free; honeypot logs fill fast. |
| `node_filesystem_files_free` | gauge | Inodes remaining. ELK indices frequently run out of inodes first. |
| `node_disk_io_now` | gauge | Number of in-flight I/O requests — saturation indicator. |
| `node_disk_reads_completed_total`, `node_disk_writes_completed_total` | counter | IOPS. |
| `node_disk_read_bytes_total`, `node_disk_written_bytes_total` | counter | Throughput. |
| `node_disk_io_time_seconds_total` | counter | Time spent doing I/O. `rate() / count(device)` > 0.7 = saturated. |
| `node_filesystem_readonly` | gauge | Filesystem was remounted read-only — usually an FS or disk failure. |

### 4️⃣ Host — Network

| Metric | Type | Description |
|---|---|---|
| `node_network_receive_bytes_total{device}` | counter | Inbound bytes; shows attacker traffic captured on each honeypot NIC. |
| `node_network_transmit_bytes_total{device}` | counter | Outbound bytes; honeypots should be near-zero — outliers may be compromised. |
| `node_network_receive_errs_total`, `node_network_transmit_errs_total` | counter | NIC errors; non-zero means cable / driver issue. |
| `node_network_drop_in_total`, `node_network_drop_out_total` | counter | Kernel drops; high drops ⇒ socket-buffer exhaustion. |
| `node_netstat_Tcp_CurrEstab` | gauge | Established TCP connections. Honeypot platforms expect a high baseline. |
| `node_netstat_Tcp_ActiveOpens`, `node_netstat_Tcp_PassiveOpens` | counter | Connection-origination side. Honeypots skew heavily `PassiveOpens`. |
| `node_sockstat_TCP_orphan`, `node_sockstat_TCP_tw` | gauge | Orphan / TIME_WAIT sockets — leaks or scan storms. |

### 5️⃣ Containers (cAdvisor)

| Metric | Type | Description |
|---|---|---|
| `container_last_seen{name=…}` | gauge | Liveness timestamp; if older than 30s the container is dead. |
| `container_cpu_usage_seconds_total{name}` | counter | Cumulative CPU time. |
| `container_memory_usage_bytes{name}` | gauge | RSS + cache; remember cache can be evicted under pressure. |
| `container_memory_working_set_bytes{name}` | gauge | The OOM-killer threshold. The most realistic "memory used". |
| `container_network_receive_bytes_total, container_network_transmit_bytes_total` | counter | Per-container network counters. |
| `container_fs_inodes_free` | gauge | Free inodes inside the container's filesystem. |
| `container_oom_events_total` | counter | **Critical** — non-zero means the kernel killed a process. |
| `container_sockets` | gauge | Open sockets in container namespace. |
| `container_tasks_state{state="running"}` | gauge | Live PIDs; spikes mean fork-bomb or PID leak. |

### 6️⃣ Application (honeynet-api)

| Metric | Type | Description |
|---|---|---|
| `http_requests_total{method, handler, status_code}` | counter | Request counter — the canonical SLO input. |
| `http_request_duration_seconds{method, handler}` | histogram | Latency histogram. Use `histogram_quantile(0.99, …)`. |
| `http_requests_inprogress{method, handler}` | gauge | Concurrency; `> nproc * 10` ⇒ saturation. |
| `http_exceptions_total{exception}` | counter | Exceptions per class. |
| `process_cpu_seconds_total`, `process_resident_memory_bytes` | gauge/counter | Process-level CPU/RSS (auto-exposed by FastAPI exporter). |
| `python_gc_collections_total{generation=0,1,2}` | counter | GC pressure; rising generation-2 count ⇒ object churn. |
| `python_info{version, implementation}` | gauge | Label-only; useful for grouping. |
| `app_dependency_up{dep="postgres\|redis\|mqtt"}` | gauge | 1 = healthy, 0 = down. Custom probe metric. |
| `app_logged_events_total{level}` | counter | Application events logged, by level. |
| `app_celery_tasks_total{status}` | counter | Tasks succeeded / failed / retried. |
| `app_active_users` | gauge | Currently-authenticated user count (sample of in-flight JWTs). |
| `app_alerts_emitted_total{severity}` | counter | Security alerts raised. |
| `app_honeypot_events_total{protocol, honeypot}` | counter | Ingested honeypot events by protocol/container. |
| `app_ai_insights_total{provider, status}` | counter | AI enrichment outcomes. |

### 7️⃣ Database — Postgres

| Metric | Type | Description |
|---|---|---|
| `pg_up` | gauge | 1 = reachable, 0 = not. Drives the topmost alert. |
| `pg_stat_activity_count{state}` | gauge | Connections by state (`active`, `idle`, `idle in transaction`). `idle in transaction > 5` is a bug. |
| `pg_stat_activity_max_tx_duration` | gauge | Longest open transaction; > 5 min usually means a stuck request. |
| `pg_locks_count` | gauge | Locks held; spikes correlate with `pg_stat_activity`. |
| `pg_stat_user_tables_seq_scan` / `idx_scan` | counter | Sequential vs index scans; rising seq_scan = missing index. |
| `pg_stat_user_tables_n_live_tup` | gauge | Row count estimate — table bloat. |
| `pg_stat_user_tables_n_dead_tup`, `pg_stat_user_tables_vacuum_count` | gauge/counter | Dead tuples / vacuum runs; auto-vacuum lag indicator. |
| `pg_database_size_bytes{datname}` | gauge | DB size. |
| `pg_stat_replication_lag_seconds` | gauge | Read-replica lag. |
| `pg_wal_lsn` | gauge | Write-ahead-log location. |
| `pg_slow_queries_total{database}` | counter | Queries > 1 s. Custom hook. |
| `pg_pool_connections{in_use, idle}` | gauge | App-side pool (`asyncpg`). |

### 8️⃣ Database — Redis

| Metric | Type | Description |
|---|---|---|
| `redis_up` | gauge | Reachable. |
| `redis_connected_clients` | gauge | Client count. |
| `redis_used_memory_bytes` | gauge | Memory; alert when `> 80 % redis_maxmemory`. |
| `redis_memory_used_peak_bytes` | gauge | Peak watermark. |
| `redis_evicted_keys_total` | counter | Evictions under memory pressure. |
| `redis_keyspace_hits_total`, `redis_keyspace_misses_total` | counter | Hit-rate = hits / (hits + misses); alert < 90 %. |
| `redis_commands_processed_total` | counter | Throughput. |
| `redis_pubsub_channels`, `redis_pubsub_patterns` | gauge | MQTT bridge subscription health. |
| `redis_latency_percentiles_usec{command}` | summary | Per-command latency. |
| `redis_blocked_clients` | gauge | Stuck on blocking commands — long-running Celery tasks. |

### 9️⃣ API metrics (REST + WS)

| Metric | Type | Description |
|---|---|---|
| `http_requests_total{method, handler, status_code}` | counter | API call counter. |
| `http_request_duration_seconds_bucket{…,le}` | histogram | Latency histogram — drives p50/p95/p99. |
| `http_requests_inprogress{handler}` | gauge | In-flight requests. |
| `http_websockets_active{path}` | gauge | Active WS connections; correlate with CPU. |
| `http_websockets_messages_total{direction, event}` | counter | WS messages sent / received. |
| `http_auth_failures_total{reason}` | counter | Failed auth — `reason ∈ {bad_pw, expired, revoked}`. |
| `http_rate_limited_total{client}` | counter | 429 responses. |
| `http_5xx_total{handler}` | counter | Server errors — feeds SLO burn-rate alerts. |

### 🔟 Honeypot / IDS / AI domain metrics

| Metric | Type | Description |
|---|---|---|
| `honeypot_unauth_attempts_total{protocol, source_country}` | counter | Unauthorised attempts — the headline attack count. |
| `honeypot_connections_active{protocol}` | gauge | Live bait sessions. |
| `honeypot_payloads_bytes_total{protocol}` | counter | Bytes ingested. |
| `ids_suricata_alerts_total{signature, severity}` | counter | Suricata signature matches. |
| `ids_zeek_notices_total{notice_type}` | counter | Zeek notices. |
| `ai_enrichment_duration_seconds{provider}` | histogram | Time spent in LLM enrichment. |
| `ai_insights_generated_total{provider, model}` | counter | Successful completions. |
| `ai_tokens_total{provider, model, type}` | counter | Prompt vs completion tokens — drives cost dashboards. |

---

## 🚨 Alerting philosophy

We follow the **Google SRE multi-window burn-rate** pattern for SLO alerts,
plus classic threshold rules for resource exhaustion. Every alert has a
`severity` label (`critical`, `warning`, `info`) and a `runbook_url`
pointing to `docs/runbook/alerts/<name>.md`.

Files:

* `observability/prometheus/rules/host.yml` — CPU, memory, disk, network
* `observability/prometheus/rules/containers.yml` — cAdvisor
* `observability/prometheus/rules/database.yml` — Postgres + Redis
* `observability/prometheus/rules/application.yml` — App + API + SLOs
* `observability/prometheus/rules/honeypot.yml` — domain-specific
* `observability/prometheus/rules/probes.yml` — blackbox
* `observability/alertmanager/alertmanager.yml` — routing / silences

---

## 🩺 Health checks

| Endpoint | Purpose | Scope |
|---|---|---|
| `GET /api/v1/health` | Liveness — process is up, can answer HTTP | per-pod |
| `GET /api/v1/ready` | Readiness — DB + Redis reachable | per-pod |
| `GET /api/v1/health/deep` | Detailed component breakdown | per-pod |
| `GET /api/v1/version` | Build info | per-pod |
| `GET /api/v1/metrics` | Prometheus exposition | per-pod |
| Blackbox `GET http://honeynet-api:8000/` | Synthetic external probe | external |
| Blackbox `tcp_connect://postgres:5432` | Synthetic TCP probe | per-service |

The blackbox probes provide **outside-in** validation: a pod reporting
"healthy" while the load-balancer can't actually reach it is one of the
most common production silent failures.

---

## 🔌 Wiring it into the FastAPI app

```python
# app/main.py
from app.core.monitoring import (
    install_metrics,
    expose_metrics,
    register_app_collectors,
)
from app.core.monitoring.health import build_health_router

install_metrics(app)                       # prometheus-fastapi-instrumentator
register_app_collectors()                  # custom collectors (DB pool, MQ, AI)
app.include_router(build_health_router(), prefix=settings.api_v1_prefix)
expose_metrics(app, path="/api/v1/metrics")
```

The `app/core/monitoring/` package contains:

* `__init__.py` — public surface
* `metrics.py` — instrumentator wiring + custom collectors (DB pool, Celery)
* `health.py` — `/health`, `/ready`, `/health/deep`
* `collectors/db.py` — asyncpg / Redis / MQTT gauges
* `collectors/app.py` — application counters
* `collectors/ai.py` — AI provider gauges

---

## 🛠️ Quick start

```bash
docker compose -f deploy/docker-compose.yml up -d \
  prometheus grafana alertmanager node-exporter cadvisor \
  postgres-exporter redis-exporter blackbox-exporter
```

Then open <http://localhost:9090> for Prometheus and
<http://localhost:3000> for Grafana (default `admin / admin` from
`deploy/.env`).

That covers every metric, every Prometheus/Grafana/Alertmanager config
file, every health check, and a field-by-field explanation of the metric
landscape.