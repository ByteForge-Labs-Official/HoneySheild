# Architecture Overview

## Bird's-eye view

```
        ┌──────────────┐
        │  Attacker    │
        └──────┬───────┘
               │ internet
        ┌──────▼───────────────────────┐
        │  Edge (gateway/)             │
        │   • Traefik  :80/:443        │
        │   • MQTT bridge :1883/:8883  │
        └──────┬───────────────────────┘
               │
   ┌───────────┼──────────────────────────────────────────┐
   │           │                                          │
   ▼           ▼                                          ▼
 Honeypots    IDS telemetry                          App plane
   │           │                                          │
   ▼           ▼                                          ▼
 Redis    ELK + Suricata + Zeek                FastAPI → PostgreSQL
 (stream/                                       │
  pub-sub)                                      ▼
                                          Celery workers
                                                 │
                                                 ▼
                                       AI log analysis service
                                                 │
                                                 ▼
                       ┌──────────────────────────────────────┐
                       │ Presentation                         │
                       │   • React Dashboard  (REST + WS)     │
                       │   • Grafana          (Postgres/ELK)  │
                       │   • Kibana           (ELK search)    │
                       └──────────────────────────────────────┘
```

## Subnet segmentation (docker networks)

| Network | Purpose | Members |
|---|---|---|
| `frontend_net` | Public-edge / dashboard | Traefik, React, Grafana, Kibana |
| `honeypot_net` | Bait services + IDS taps | All honeypots, Suricata, Zeek |
| `data_net` | Internal data plane | Postgres, Redis, Elasticsearch, Logstash, FastAPI, workers |
| `mgmt_net` | Operator-only reverse channel | FastAPI admin, AI service |

Edge services are the only ones exposed to the host port map.  Honeypot containers
have **no outbound** route (enforced by iptables egress block in `deploy/hardening/`).

## Data flow

1. **Capture** — Traefik forwards public bait ports to the right honeypot container
   and mirrors raw PCAP to Suricata + Zeek.
2. **Enrich** — each honeypot container writes its native log format to a shared
   Redis stream (`attacks:raw`) *and* its own JSON file under `data/honeypot-logs/`.
3. **Normalize** — a Celery worker (`worker.normalize`) reads from the stream,
   enriches with GeoIP / threat-intel lookups, and writes canonical rows into
   PostgreSQL (`attacks`, `sessions`, `events`, `iocs`).
4. **Detect** — Suricata + Zeek logs are shipped by Filebeat into Logstash, which
   indexes them in Elasticsearch.
5. **Analyze** — the AI service periodically scans a window of recent attacks and
   emits MITRE ATT&CK tags + narrative summaries into PostgreSQL.
6. **Visualize** — the React dashboard subscribes to a WebSocket channel
   (`/api/v1/ws/attacks`) backed by Redis pub/sub; Grafana pulls time-series from
   PostgreSQL aggregates; Kibana exposes raw IDS search.

## Concurrency & scaling

* FastAPI workers default to 2 (`BACKEND_WORKERS`) and scale horizontally.
* Celery worker count defaults to `2` and can scale to N — Redis backs both
  broker and result backend.
* Honeypots are independently scalable; each ships with a `HPA`-style compose profile.

## Persistence

| Volume | Driver | Contents |
|---|---|---|
| `pg_data` | local | PostgreSQL data |
| `redis_data` | local | Redis AOF/RDB |
| `es_data` | local | Elasticsearch indices |
| `suricata_logs` | bind (`data/`) | IDS eve.json + pcap |
| `zeek_logs` | bind (`data/`) | Zeek conn / http / notice logs |
| `honeypot_logs` | bind (`data/`) | per-honeypot native logs |

Bind mounts (`data/`) let operators inspect PCAP from the host even if Elasticsearch
is degraded.
