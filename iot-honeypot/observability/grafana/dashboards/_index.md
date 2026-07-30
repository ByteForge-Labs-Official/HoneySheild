# Honeynet Grafana dashboards

Provisioned automatically from this directory via
`/etc/grafana/provisioning/dashboards/dashboards.yml`.

| File | UID | Purpose |
|------|-----|---------|
| `01-overview.json`     | `honeynet-overview`     | High-level fleet summary — CPU/mem/disk/net + honeypot attempt count |
| `02-api.json`          | `honeynet-api`          | RPS, latency percentiles, error rate, Celery outcomes, AI volume |
| `03-database.json`     | `honeynet-database`     | Postgres connections, TPS, replication lag, Redis memory / hit-rate |
| `04-containers.json`   | `honeynet-containers`   | cAdvisor per-container CPU / memory / network / OOM |
| `05-honeypot.json`     | `honeynet-domain`       | Domain metrics — attempts by protocol & country, Suricata alerts |
| `06-alerts.json`       | `honeynet-alerts`       | Live firing alerts table (uses Prometheus as data source) |

## Threshold dashboards

Each row uses `fieldConfig.defaults.thresholds` aligned with the
Prometheus rules in `observability/prometheus/rules/`. Panels light up
green/yellow/red in the same way that alerts page — Grafana becomes a
visual mirror of the alertmanager.