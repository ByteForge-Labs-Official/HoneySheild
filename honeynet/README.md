# 🛡️ IoT Honeynet Research Platform

A modular, Docker-first honeypot research platform that emulates IoT devices, captures
attacks across multiple protocols, and ships a real-time analytics dashboard backed by
PostgreSQL, Redis, MQTT, ELK, Suricata, Zeek, and Grafana.

---

## ✨ Highlights

| Capability | Implementation |
|---|---|
| Multi-protocol honeypots | SSH, Telnet, HTTP, RTSP, MQTT, Modbus, UPnP |
| Network IDS | Suricata + Zeek feeding ELK |
| REST + WebSocket API | FastAPI (Python 3.12), async + Celery workers |
| Real-time dashboard | React 18 + Vite + Recharts/Mapbox/Vis |
| AI log analysis | pluggable providers (local / Ollama / OpenAI) |
| Storage | PostgreSQL 16 (canonical) + Redis 7 (stream/pub-sub) |
| Deployment | one-shot `docker compose` with hardening baked in |

---

## 🗂️ Layout

```
honeynet/
├── backend/                 FastAPI app (REST + WS + workers)
├── frontend/                React + Vite dashboard
├── honeypots/               per-service bait containers + profiles
├── ids/                     Suricata & Zeek configs/rules
├── observability/           Grafana, Kibana, ELK, Prometheus
├── gateway/                 Traefik entry + MQTT bridge
├── db/                      Postgres init + Redis config
├── deploy/                  compose, env, hardening scripts
├── data/                    runtime volumes (git-ignored)
└── docs/                    architecture, runbook, API, security
```

See [`docs/architecture/00-overview.md`](docs/architecture/00-overview.md) for the full
component map.

---

## 🚀 Quick start

```bash
cp .env.example .env                 # then edit secrets
docker compose -f deploy/docker-compose.yml pull
docker compose -f deploy/docker-compose.yml up -d
./deploy/scripts/bootstrap.sh
```

UI endpoints (after bootstrap):

* Dashboard — `http://localhost/`
* FastAPI — `http://localhost:8000/api/v1/...` (Swagger at `/docs`)
* Grafana — `http://localhost:3000/`
* Kibana — `http://localhost:5601/`

---

## 🔐 Security

This is an **active deception platform**.  Every honeypot container runs with
`read_only`, `cap_drop:[ALL]`, `no-new-privileges`, and an outbound blocklist via
iptables.  See [`docs/security/threat-model.md`](docs/security/threat-model.md).

---

## 📚 Documentation

* [`docs/architecture/`](docs/architecture)
* [`docs/runbook/`](docs/runbook)
* [`docs/api/`](docs/api)
* [`docs/security/`](docs/security)

---

## 📄 License

MIT (see `LICENSE`).
