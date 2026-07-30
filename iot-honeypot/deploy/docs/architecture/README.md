# 🐳 Containerization Reference

A single-pass map of every container in `deploy/docker-compose.yml`, why it exists,
how it talks to the others, and where state lives. Read this before changing
the topology.

> **TL;DR.** The Java honeypot stays untouched. A Python **relay** tails its
> SQLite + log file and ships rows to **Postgres + Redis**. A **gateway**
> (Caddy + Cloudflare DNS-01) is the only component that accepts TCP from the
> outside world. Everything else — Prometheus, Grafana, Alertmanager, exporters
> — sits on the observability profile and is optional.

---

## 1. Why every container exists

| # | Service | Purpose | Runs in profile |
|---|---------|---------|-----------------|
| 1 | `honeypot` | The Java/MINA SSH+HTTP+RTSP low-interaction IoT honeypot. Captures brute-force attempts, fake-shell sessions, and protocol probes. Writes to `/data/honeypot.db` (SQLite) and `/data/honeypot.log` (logback JSON). | `core` (default) |
| 2 | `relay` | Python 3.12 side-car. Polls the honeypot's SQLite every 10s and watches the log file with `inotify`. Forwards every new row/line to **Postgres** (`events.attack` hypertable) and **Redis Streams** (`honeynet:events:*`). Exposes Prometheus metrics on `:9101`. | `core` |
| 3 | `postgres` | Postgres 16 with the **TimescaleDB** extension. Canonical store for attack events. 3 roles (`honeynet_app`, `honeynet_ro`, `relay`), 3 schemas (`events`, `honeypots`, `ai`), 1-hour TimescaleDB hypertable for `events.attack`. | `core` |
| 4 | `redis` | Redis Stack Server 7.4. Used as the **low-latency stream** (`XADD` into consumer groups) so subscribers (Grafana, future workers) can tail events without hammering Postgres. AOF everysec, 512 MB cap. | `core` |
| 5 | `gateway` | Caddy 2.7 (built with `xcaddy` + `caddy-dns/cloudflare`). Reverse-proxy + TLS terminator. 4 vhosts: dashboard, grafana, alertmanager, prometheus — all behind basic-auth. Only container with `ports: 80/443` mapped to the host. | `core` |
| 6 | `prometheus` | Metrics scraper. 7 jobs: self, node, relay, postgres, redis, caddy, blackbox-ssh. Eval `honeynet.core` rule group every 30s. | `observability` |
| 7 | `grafana` | Dashboarding. The Grafana **own DB** is Postgres (`grafana` DB on `postgres:5432`). Sources: Prometheus + Postgres + Redis. | `observability` |
| 8 | `alertmanager` | Alert routing. PagerDuty for `critical`, three Slack channels (security, ops, dba) by `tier`, default email receiver. 3 inhibit_rules suppress cascading noise. | `observability` |
| 9 | `node-exporter` | Host metrics (CPU, memory, disk, network, fsstats). Mounted `:ro` of `/`, `/proc`, `/sys`. | `observability` |
| 10 | `postgres-exporter` | Postgres metrics (connections, replication lag, locks, tuple activity, per-table I/O). Connects with the `honeynet_ro` role. | `observability` |
| 11 | `redis-exporter` | Redis metrics incl. streams and modules. Connects with `requirepass`. | `observability` |
| 12 | `blackbox-exporter` | Synthetic probes. The `ssh_banner` module regexes `^SSH-2.0-` against the honeypot so a misconfigured SSH banner triggers an alert. | `observability` |

If you only ever need the honeypot + persistence:

```bash
docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d
```

To bring up the dashboards:

```bash
docker compose -f deploy/docker-compose.yml --profile observability --env-file deploy/.env up -d
```

---

## 2. How containers communicate

There are **three bridges** with strict access rules. No `links:` are used —
service-name DNS is what services resolve.

```
                  ┌────────────── INTERNET (Cloudflare) ──────────────┐
                  │                                                   │
                  │  TLS (DNS-01) → 80/443 on host → gateway (Caddy)   │
                  └───────────────────────┬───────────────────────────┘
                                          │
                       ┌──────────────────┴──────────────────┐
                       │             edge-net               │  ICC: on
                       │  gateway, grafana, alertmanager     │
                       └──────┬──────────────────────┬───────┘
                              │                      │
                              │                      │
        ┌─────────────────────┴──┐         ┌────────┴──────────────────────┐
        │       bait-net         │         │           ops-net             │  ICC: on
        │  honeypot, relay,      │         │  postgres, redis, relay,      │
        │  gateway               │         │  prometheus, grafana,         │
        │  ICC: OFF              │         │  alertmanager, exporters      │
        │  internal: true        │         │  internal: true               │
        └────────────────────────┘         └───────────────────────────────┘
```

### Per-service network membership

| Service | bait-net | ops-net | edge-net |
|---------|:---:|:---:|:---:|
| honeypot | ✅ |   |   |
| relay | ✅ | ✅ |   |
| postgres |   | ✅ |   |
| redis |   | ✅ |   |
| gateway | ✅ | ✅ | ✅ |
| prometheus |   | ✅ |   |
| grafana |   | ✅ | ✅ |
| alertmanager |   | ✅ | ✅ |
| node-exporter |   | ✅ |   |
| postgres-exporter |   | ✅ |   |
| redis-exporter |   | ✅ |   |
| blackbox-exporter |   | ✅ |   |

### Traffic flows

1. **Attacker → honeypot.** The gateway forwards `HONEYPOT_DOMAIN:443` to `honeypot:2222` over `bait-net`. The honeypot never listens on the host directly.
2. **Honeypot writes.** Java writes to `/data/honeypot.db` (SQLite, WAL) and `/data/honeypot.log` (JSON). Both files are on the `honeypot-data` named volume.
3. **Relay ships.** The relay mounts `honeypot-data:ro` and pushes new rows to `postgres:5432` (DML via `relay` role) and to `redis:6379` (`XADD honeynet:events:attack`).
4. **Grafana reads.** Grafana reaches Postgres via `postgres:5432` for the dashboard panels and Grafana's own DB; Redis via `redis:6379` to show live stream depth.
5. **Prometheus scrapes.** Prometheus reaches every exporter on `ops-net`. The relay's `/metrics` lives on `ops-net` (the relay is dual-homed).
6. **Alertmanager → PagerDuty / Slack / SMTP.** Outbound only. Webhook URLs use the appropriate secrets.

---

## 3. Ports

Only `gateway` publishes to the host. Everything else is reachable only on the
internal bridges.

### Host-published (only `gateway`)

| Host port | Container | Service | Notes |
|---:|---:|---|---|
| `80` | 80 | Caddy | Plain-HTTP → permanent redirect to HTTPS. |
| `443` | 443 | Caddy | TLS terminated (Cloudflare DNS-01). Holds all 4 vhosts. |

### Container-internal ports (reachable on `edge-net` / `ops-net` / `bait-net`)

| Service | Port | Protocol | Reachability |
|---|---:|---|---|
| honeypot | 2222 | TCP (SSH) | `bait-net` — gateway only |
| honeypot | 8080 | TCP (HTTP) | `bait-net` — gateway only |
| honeypot | 554  | TCP (RTSP) | `bait-net` — gateway only |
| relay | 9101 | TCP (Prometheus) | `ops-net` |
| postgres | 5432 | TCP (Postgres) | `ops-net` |
| redis | 6379 | TCP (Redis) | `ops-net` |
| gateway | 2019 | TCP (Caddy admin API) | `ops-net` (bound to `127.0.0.1` only) |
| prometheus | 9090 | TCP (web UI) | `ops-net` (proxied by gateway) |
| grafana | 3000 | TCP (web UI) | `ops-net` (proxied by gateway) |
| alertmanager | 9093 | TCP (web UI) | `ops-net` (proxied by gateway) |
| node-exporter | 9100 | TCP (Prometheus) | `ops-net` |
| postgres-exporter | 9187 | TCP (Prometheus) | `ops-net` |
| redis-exporter | 9121 | TCP (Prometheus) | `ops-net` |
| blackbox-exporter | 9115 | TCP (Prometheus) | `ops-net` |

> **Important.** The honeypot is **never** reachable from the host. The only
> way to reach port 2222 is `ssh -p 443 ${HONEYPOT_DOMAIN}` *through* the
> gateway, or by `docker exec honeynet-honeypot` from inside the bridge.

---

## 4. Volumes

Eight named volumes. Bind-mounts are deliberately avoided — they leak host
permissions into the container.

| Volume | Used by | R/W | What’s inside |
|---|---|---|---|
| `honeypot-data` | honeypot (RW), relay (RO) | RW for honeypot, RO for relay | `honeypot.db` (SQLite, WAL mode), `honeypot.log` (logback JSON). The relay reads both. |
| `postgres-data` | postgres | RW | `/var/lib/postgresql/data` — Postgres cluster. |
| `redis-data` | redis | RW | `/data` — AOF + RDB snapshots. |
| `prometheus-data` | prometheus | RW | `/prometheus` — TSDB + WAL. |
| `grafana-data` | grafana | RW | `/var/lib/grafana` — provisioning cache, plugins. |
| `alertmanager-data` | alertmanager | RW | `/alertmanager` — silences + notification log. |
| `caddy-data` | gateway | RW | `/data` — Caddy certificates, ACME account, OCSP staples. |
| `caddy-config` | gateway | RW | `/config` — Caddy autosaved JSON config. |

### Configuration files (bind-mounts, read-only)

| Source path | Mounted into | Service | Mode |
|---|---|---|---|
| `deploy/postgres/postgresql.conf` | `/etc/postgresql/postgresql.conf` | postgres | RO |
| `deploy/postgres/init/*.sql` | `/docker-entrypoint-initdb.d/` | postgres | RO |
| `deploy/redis/redis.conf` | `/usr/local/etc/redis/redis.conf` | redis | RO |
| `deploy/observability/prometheus/prometheus.yml` | `/etc/prometheus/prometheus.yml` | prometheus | RO |
| `deploy/observability/prometheus/rules/*.yml` | `/etc/prometheus/rules/` | prometheus | RO |
| `deploy/observability/alertmanager/alertmanager.yml` | `/etc/alertmanager/alertmanager.yml` | alertmanager | RO |
| `deploy/observability/grafana/grafana.ini` | `/etc/grafana/grafana.ini` | grafana | RO |
| `deploy/observability/exporters/web-config.yml` | `/etc/prometheus_exporter.yml` | postgres-exporter | RO |
| (gossamer) | `/etc/redis_exporter.env` | redis-exporter | env_file |
| `deploy/gateway/Caddyfile` | `/etc/caddy/Caddyfile` | gateway | RO |
| `deploy/gateway/index.html` | `/srv/index.html` | gateway | RO |
| `deploy/relay/.dockerignore` etc. | — | relay | build-time only |

### Secrets (tmpfs at `/run/secrets`)

13 secrets. Generated by `deploy/secrets/generate.sh` (or the
`deploy/secrets/README.md` recipe).

| Secret | Used by | Purpose |
|---|---|---|
| `postgres_password` | postgres | `POSTGRES_PASSWORD` for the superuser. |
| `postgres_ro_password` | postgres-exporter | `honeynet_ro` role login. |
| `relay_password` | postgres | `relay` role login (used by the relay). |
| `grafana_admin_password` | grafana | `GF_SECURITY_ADMIN_PASSWORD`. |
| `grafana_secret_key` | grafana | `GF_SECURITY_SECRET_KEY` (cookie signing). |
| `grafana_db_password` | grafana | Login to the `grafana` Postgres DB. |
| `am_basic_auth` | alertmanager | `htpasswd` line for the Alertmanager web UI. |
| `prom_basic_auth` | prometheus | `htpasswd` line for the Prometheus web UI. |
| `caddy_cloudflare_token` | gateway | Cloudflare DNS-01 API token (zone:DNS:Edit on the 4 domains). |
| `pagerduty_key` | alertmanager | PagerDuty Events API v2 routing key. |
| `slack_webhook_sec` | alertmanager | Slack webhook for `tier=security`. |
| `slack_webhook_ops` | alertmanager | Slack webhook for `tier=host`. |
| `slack_webhook_dba` | alertmanager | Slack webhook for `tier=database`. |

> **Note.** `postgres` is intentionally given only `postgres_password`; the
> `relay_password` and `postgres_ro_password` are claimed by the relay and
> postgres-exporter roles respectively, but the *creation* of those roles
> happens in `init/01-honeynet-db.sql` with the matching passwords from the
> `.env`.

---

## 5. Networking rules

### Why three networks?

| Network | CIDR (default) | `internal` | `driver` | ICC | Purpose |
|---|---|---|---|---|---|
| `bait-net` | `172.30.0.0/24` | `true` | `bridge` | **off** | Honeypot blast-radius. No outbound (no internet), no peer-to-peer. Only the gateway in. |
| `ops-net` | `172.30.1.0/24` | `true` | `bridge` | on | Internal services that need to talk: postgres ↔ relay ↔ exporters ↔ prometheus ↔ grafana. |
| `edge-net` | `172.30.2.0/24` | `false` | `bridge` | on | Anything reachable from the gateway / observability web UIs. |

`internal: true` means **no NAT to the host internet** — the bait-net cannot
phone home even if the honeypot is compromised (this is defence-in-depth on
top of `cap_drop: [ALL]` + `no-new-privileges`).

### Hardening matrix

| Service | `read_only` | `cap_drop` | `no-new-privileges` | `seccomp` | `pids_limit` | resource limits |
|---|:---:|:---:|:---:|:---:|:---:|---|
| honeypot | ✅ | ALL | ✅ | default | 256 | 0.5/256M |
| relay | ✅ | ALL | ✅ | default | 128 | 0.25/128M |
| postgres | ✅ | ALL | ✅ | default | 200 | 1.0/512M |
| redis | ✅ | ALL | ✅ | default | 128 | 0.5/256M |
| gateway |   | ALL | ✅ | default | 256 | 0.5/256M |
| prometheus | ✅ | ALL | ✅ | default | 256 | 0.5/512M |
| grafana | ✅ | ALL | ✅ | default | 256 | 0.5/256M |
| alertmanager | ✅ | ALL | ✅ | default | 128 | 0.25/128M |
| node-exporter | ✅ | ALL | ✅ | default | 64 | 0.1/32M |
| postgres-exporter | ✅ | ALL | ✅ | default | 64 | 0.1/32M |
| redis-exporter | ✅ | ALL | ✅ | default | 64 | 0.1/32M |
| blackbox-exporter | ✅ | ALL | ✅ | default | 64 | 0.1/32M |

Gateway intentionally drops `ALL` capabilities but **does not** run
`read_only` because Caddy needs to write certs into `/data/caddy` and update
`/config/caddy/autosave.json`.

### DNS resolution

Docker's embedded DNS (`127.0.0.11:53`) resolves service names to the bridge
IP. There is no `links:` anywhere; every cross-service reference uses the
service name (`postgres:5432`, `redis:6379`, `honeypot:2222`).

### ICMP / external reachability

- `bait-net` is `internal: true` → **no** internet egress.
- `ops-net` is `internal: true` → **no** internet egress (exporters talk to
  peers only; outbound updates must be done by `docker exec`).
- `edge-net` is **not** internal → only transit is from Caddy to the
  Cloudflare API for cert renewal (DNS-01, on port 443).

---

## 6. Health-checks & restart

Every service has both:

- `healthcheck.test` — what command runs.
- `restart: unless-stopped` — what happens when the host reboots.
- `deploy.restart_policy.condition: on-failure` with `max_attempts: 5` and
  `delay: 5s` — for crashed processes.

Default healthcheck intervals are 30s with 3 retries. The relay exposes
`/healthz` which returns 200 only when the DB tail + log tail are both
healthy — used by both Docker and Prometheus.

---

## 7. Local validation

The compose file was parsed with `python -m pip install --user pyyaml && python -c "import yaml; yaml.safe_load(...)"` and the dump is:

| Object | Count | Names |
|---|---|---|
| services | 12 | honeypot, relay, postgres, redis, gateway, prometheus, grafana, alertmanager, node-exporter, postgres-exporter, redis-exporter, blackbox-exporter |
| networks | 3 | bait-net, ops-net, edge-net |
| volumes | 8 | honeypot-data, postgres-data, redis-data, prometheus-data, grafana-data, alertmanager-data, caddy-data, caddy-config |
| secrets | 13 | (see table above) |
| healthchecks | 12 | every service |
| restart policies | 12 | every service |

If `docker compose config` is available, run it as the authoritative check:

```bash
docker compose -f deploy/docker-compose.yml --env-file deploy/.env.example config -q && echo OK
```

---

## 8. Where to look next

- Diagrams in Mermaid: [`docs/architecture/containers.mmd`](containers.mmd), [`docs/architecture/request-flow.mmd`](request-flow.mmd), [`docs/architecture/network.mmd`](network.mmd), [`docs/architecture/volumes.mmd`](volumes.mmd).
- Per-service deeper dive: each container has a `Dockerfile` next to its config in `deploy/<service>/`.
- Alert rules: [`deploy/observability/prometheus/rules/honeynet.yml`](../observability/prometheus/rules/honeynet.yml).
- Runbook: [`docs/runbook/bootstrap.md`](../../runbook/bootstrap.md).
