# syntax=docker/dockerfile:1.6
# ============================================================================
# Honeynet — Postgres 16 with TimescaleDB for time-series attack data.
# ----------------------------------------------------------------------------
# Why a custom image
#   The stock postgres:16 image can't load the TimescaleDB shared object
#   (it's not in the standard image).  We extend it with the official
#   .deb from packagecloud and pre-create the honeynet database with the
#   `timescaledb` extension enabled.
# ============================================================================
FROM postgres:16-bookworm

ARG TARGETARCH

RUN set -eux \
 && apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
 && install -d /usr/share/keyrings \
 && curl -fsSL https://packagecloud.io/timescale/timescaledb/gpgkey \
        | gpg --dearmor -o /usr/share/keyrings/timescaledb.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/timescaledb.gpg] https://packagecloud.io/timescale/timescaledb/debian/ bookworm main" \
        > /etc/apt/sources.list.d/timescaledb.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends timescaledb-2-postgresql-16 \
 && apt-get purge -y --auto-remove curl gnupg \
 && rm -rf /var/lib/apt/lists/*

# Pre-create the database & extension so the relay can connect on first boot.
COPY init/01-honeynet-db.sql /docker-entrypoint-initdb.d/01-honeynet-db.sql
COPY init/02-extensions.sql  /docker-entrypoint-initdb.d/02-extensions.sql

# Tighten server defaults — the honeynet doesn't need exotic locales.
RUN sed -i \
    -e "s/^#shared_preload_libraries = ''/shared_preload_libraries = 'timescaledb'/" \
    -e "s/^#max_connections = 100/max_connections = 200/" \
    -e "s/^#log_min_duration_statement = -1/log_min_duration_statement = 500ms/" \
    /usr/share/postgresql/postgresql.conf.sample

EXPOSE 5432/tcp
USER postgres

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=10 \
    CMD pg_isready -U "${POSTGRES_USER:-honeynet}" -d "${POSTGRES_DB:-honeynet}" || exit 1