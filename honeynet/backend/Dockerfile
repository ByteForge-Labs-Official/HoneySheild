# ============================================================================
# Honeynet backend — FastAPI + Celery worker base image
# ============================================================================
# Multi-stage build:
#   builder  — installs deps in a venv, then copies to a slim runtime layer
#   runtime  — non-root, distroless-style slim image with only the venv
# ============================================================================
ARG PYTHON_VERSION=3.12.4
ARG POETRY_VERSION=1.8.3

FROM python:${PYTHON_VERSION}-slim-bookworm AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential gcc libpq-dev curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip wheel \
 && /opt/venv/bin/pip install --no-cache-dir .

# ----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
ARG UID=10001
ARG GID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH=/app

# OS-level hardening: create non-root user with no shell, no home.
RUN groupadd --system --gid ${GID} honeynet \
 && useradd  --system --uid ${UID} --gid honeynet \
             --home /nonexistent --shell /sbin/nologin --no-create-home honeynet \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
        libpq5 curl tini ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /app /static \
 && chown -R honeynet:honeynet /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=honeynet:honeynet app /app/app
COPY --chown=honeynet:honeynet alembic.ini /app/alembic.ini
COPY --chown=honeynet:honeynet entrypoint.sh /app/entrypoint.sh
RUN chmod 0550 /app /app/app && chmod 0750 /app/entrypoint.sh

USER honeynet
WORKDIR /app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/api/v1/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/app/entrypoint.sh"]
CMD ["api"]
