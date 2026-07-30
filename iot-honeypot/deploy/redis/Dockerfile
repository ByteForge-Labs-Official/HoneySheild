# syntax=docker/dockerfile:1.6
# ============================================================================
# Honeynet — Redis 7 with the redis-stack modules baked in.
# ----------------------------------------------------------------------------
# Why a custom image
#   We want RedisJSON (so the relay can ship structured payloads) and
#   RedisBloom (so the dashboard can dedupe attacker fingerprints) without
#   running two side-cars.  The official `redis/redis-stack-server` image
#   already bundles them — we only override the config and entrypoint.
# ============================================================================
FROM redis/redis-stack-server:7.4.0-v0

# Production-tuned config — AOF on, no save snapshots, maxmemory enforced.
COPY redis.conf /usr/local/etc/redis/redis.conf

USER redis
EXPOSE 6379/tcp

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD redis-cli -p 6379 PING | grep -q PONG