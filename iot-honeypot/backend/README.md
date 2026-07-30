# Honeynet Backend (FastAPI)

Production-grade REST API for the IoT Honeynet Research Platform.

## Stack

| Concern | Choice |
|---|---|
| Web framework | FastAPI 0.111 (ASGI, OpenAPI 3) |
| ORM | SQLAlchemy 2 async + asyncpg |
| Migrations | Alembic |
| Auth | JWT (HS256) + bcrypt |
| Settings | pydantic-settings v2 |
| Logging | structlog (JSON in prod, pretty in dev) |
| Caching / broker | Redis (asyncio client) |
| Background tasks | Celery 5 (Beat) |
| Tracing | OpenTelemetry FastAPI instrumentation |
| Metrics | prometheus-fastapi-instrumentator |
| Linting / typing | Ruff + mypy |

## Folder layout

```
backend/
├── app/
│   ├── api/                # routers (v1 aggregator)
│   │   ├── deps/           # auth/role dependencies
│   │   └── v1/             # auth, honeypots, events, alerts, ai, health
│   ├── core/               # config, security, logging, errors, middleware
│   ├── db/                 # session + models + repositories
│   ├── integrations/       # redis, mqtt, ids (suricata/zeek), ai
│   ├── schemas/            # Pydantic DTOs
│   ├── scripts/            # one-shot scripts (seed_admin, …)
│   ├── services/           # business logic
│   ├── workers/            # Celery tasks
│   └── main.py             # FastAPI factory + middleware wiring
├── alembic/                # migrations
├── tests/                  # pytest + httpx
├── scripts/                # dev / migration / seed helpers
├── Dockerfile
├── pyproject.toml
└── .env.example
```

## Quick start (local dev)

```bash
cp .env.example .env
pip install -e ".[dev]"
bash scripts/migrate.sh        # alembic upgrade head
bash scripts/run-dev.sh        # uvicorn with --reload
```

Open `http://localhost:8000/docs` for Swagger.

## Quick start (Docker)

```bash
docker build -t honeynet-backend .
docker run --rm -p 8000:8000 --env-file .env honeynet-backend
```

## Endpoints

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET  | `/api/v1/health`            | none | Liveness |
| GET  | `/api/v1/ready`             | none | Readiness (DB+Redis) |
| GET  | `/api/v1/version`           | none | Build info |
| POST | `/api/v1/auth/register`     | none | Returns JWT pair |
| POST | `/api/v1/auth/login`        | none | Returns JWT pair |
| POST | `/api/v1/auth/refresh`      | none | New access token |
| GET  | `/api/v1/auth/me`           | JWT  | Current user |
| GET  | `/api/v1/honeypots`         | JWT + analyst/admin | List |
| POST | `/api/v1/honeypots`         | JWT + admin | Create |
| PATCH | `/api/v1/honeypots/{id}`   | JWT + admin | Update |
| DELETE | `/api/v1/honeypots/{id}`  | JWT + admin | Delete |
| POST | `/api/v1/events/{hp}/events`| API key / internal | Ingest |
| GET  | `/api/v1/events/{hp}/events`| JWT + analyst | List |
| GET  | `/api/v1/events/recent`     | JWT + analyst | Across all |
| GET  | `/api/v1/alerts`            | JWT + analyst | Recent alerts |
| GET  | `/api/v1/ai/events/{id}/insights` | JWT + analyst | AI summaries |

## Configuration

All settings are typed in `app/core/config/settings.py` and sourced from env (or `.env`). The single accessor is `get_settings()` (cached). Required vars: `JWT_SECRET`, `SESSION_SECRET`, `POSTGRES_PASSWORD`, `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `FLOWER_PASSWORD`.

## Migrations

```bash
# autogenerate after a model change
alembic revision --autogenerate -m "add field x"

# apply
alembic upgrade head

# roll back one step
alembic downgrade -1
```

## Tests

```bash
pytest                 # unit + integration (sqlite in-memory)
pytest --cov=app       # with coverage
ruff check .           # lint
mypy app               # type check
```

## Production checklist

- `APP_ENV=production`
- `JWT_SECRET`, `SESSION_SECRET`, `FLOWER_PASSWORD` from a secrets manager
- `CORS_ORIGINS` explicit (no `*`)
- `ALLOWED_HOSTS` explicit
- Run behind a TLS-terminating reverse proxy (Traefik / nginx)
- Run worker: `celery -A app.workers.celery_app.celery_app worker -l info`
- Run scheduler: `celery -A app.workers.celery_app.celery_app beat -l info`
- Run Flower (optional): `celery -A app.workers.celery_app.celery_app flower --basic_auth="${FLOWER_USER}:${FLOWER_PASSWORD}"`
- Health check: `GET /api/v1/health` returns `{"status":"ok",...}`
- Metrics: `GET /api/v1/metrics` (Prometheus exposition)