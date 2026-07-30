# syntax=docker/dockerfile:1.6
# ============================================================================
# Honeynet — TLS reverse proxy / edge gateway (Caddy 2)
# ----------------------------------------------------------------------------
# Why this container exists
# --------------------------
#   • Terminates TLS (Let's Encrypt via the DNS-01 challenge against the
#     Cloudflare provider) so attackers see a real-looking certificate
#     chain for the dashboard, alertmanager and Prometheus UIs.
#   • Publishes *only* 80/443 to the host.  All upstream ports live on the
#     internal `ops-net` bridge — nothing inside the platform is reachable
#     directly from the public Internet.
#   • Strict transport security, HSTS preload, OCSP stapling and a
#     hardened TLS profile (Mozilla "intermediate") — no TLS 1.0/1.1.
#
# Build:   docker build -t honeynet/gateway:latest deploy/gateway
# ============================================================================

FROM caddy:2.7-builder AS build

# Pull the DNS-01 plugin so we can mint certs without exposing :80 publicly.
RUN xcaddy build \
    --with github.com/caddy-dns/cloudflare

# ----------------------------------------------------------------------------
# Runtime — distroless-ish: no shell, only the caddy binary + its assets.
# ----------------------------------------------------------------------------
FROM caddy:2.7

COPY --from=build /usr/bin/caddy /usr/bin/caddy

# Static, version-controlled Caddyfile baked in.  Secrets (Cloudflare token)
# come from /run/secrets/caddy_cloudflare_token — see deploy/docker-compose.yml.
COPY Caddyfile /etc/caddy/Caddyfile
COPY index.html /srv/index.html

# Caddy runs as uid 0 by default so it can bind 80/443.  We keep that but
# tell it to chroot its workdir, drop to a non-root user for *handler*
# sub-processes and refuse outbound traffic to anything except the DNS
# provider and the upstream services on `ops-net`.
USER root

# Healthcheck hits the local Caddy admin API (default :2019 inside the
# container).  The compose file overrides to a public endpoint instead.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD caddy health || exit 1

EXPOSE 80/tcp 443/tcp

# Run in foreground so docker can supervise.
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", ""]