# syntax=docker/dockerfile:1.6
# ============================================================================
# Honeynet — Side-car relay
# ----------------------------------------------------------------------------
# Why this container exists
# --------------------------
#   The Java honeypot persists everything to an embedded SQLite database
#   and writes structured logs to /data/honeypot.log.  Both are useless
#   for analytics at scale (no concurrent readers, no JOINs against
#   Suricata or the dashboard's user table, no time-series).
#
#   This relay:
#     1. tails /data/honeypot.log via inotify,
#     2. reads the SQLite WAL every 10 s,
#     3. ships both streams into the central Postgres + Redis cache,
#     4. exposes Prometheus metrics on :9101 so the platform can
#        graph ingest lag.
#
#   Running it as a side-car keeps the honeypot JVM exactly as it was —
#   no JDBC driver, no Postgres awareness, no metric library in the
#   attack surface.
# ============================================================================

FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim-bookworm

# Non-root runtime user (matches honeypot — uid 10001).
RUN groupadd -g 10001 honeypot \
    && useradd  -u 10001 -g honeypot -M -s /sbin/nologin relay

# Copy the pre-built wheels from the builder stage.
COPY --from=builder /install /usr/local

# Source — small, read-only at runtime via `read_only: true` in compose.
COPY app /opt/relay/app

USER relay
WORKDIR /opt/relay

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    RELAY_LOG_LEVEL=INFO

EXPOSE 9101/tcp

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:9101/healthz',timeout=3).status==200 else 1)"

CMD ["python", "-m", "app.main"]