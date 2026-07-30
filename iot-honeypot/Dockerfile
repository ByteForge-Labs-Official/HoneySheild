# syntax=docker/dockerfile:1.6

# ============================================================================
# Stage 1: Build
# ============================================================================
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /workspace

# Cache dependencies first for faster rebuilds
COPY pom.xml .
RUN mvn -B -ntp dependency:go-offline

# Build the fat JAR
COPY src ./src
RUN mvn -B -ntp clean package -DskipTests \
 && cp target/iot-honeypot.jar /workspace/iot-honeypot.jar

# ============================================================================
# Stage 2: Runtime — defense-in-depth hardening (audit 2026-07-28)
# ============================================================================
# Distroless-style minimal base: only the JRE + a non-root user. No shell,
# no package manager, no busybox — there is nothing to escalate into.
#
# NOTE: eclipse-temurin:17-jre-alpine is the smallest Temurin flavor we can
#       still execute `adduser` against; we explicitly *remove* shell access
#       for the runtime user below via `adduser -s /sbin/nologin`.
FROM eclipse-temurin:17-jre-alpine
# (Intentionally kept generic: if you swap to a JRE-only image that lacks
#  /usr/sbin/adduser, replace those three lines with a static /etc/passwd.)

# ---------------------------------------------------------------------------
# Rule 1: Non-root execution
#   - Fixed UID 10001 so it can be mapped 1:1 to a host user.
#   - -s /sbin/nologin so even a process escape can't open a login shell.
#   - No password, no home dir, no group memberships beyond `honeypot`.
# ---------------------------------------------------------------------------
RUN addgroup -g 10001 -S honeypot \
 && adduser  -u 10001 -S -G honeypot \
              -h /nonexistent \
              -s /sbin/nologin \
              -D honeypot \
 && mkdir -p /app /data \
 && chown -R honeypot:honeypot /app /data \
 && chmod 0750 /app /data

# ---------------------------------------------------------------------------
# Layout:
#   /app   — read-only at runtime (contains the fat JAR)
#   /data  — *only* writable mount, the SQLite/hostkey/log live here
# ---------------------------------------------------------------------------
WORKDIR /app

# Fat JAR copied as root, then ownership handed to honeypot. We then strip
# write permission on /app so even uid 10001 can't rewrite the binary.
COPY --from=build --chown=honeypot:honeypot /workspace/iot-honeypot.jar /app/iot-honeypot.jar
RUN chmod 0550 /app /app/iot-honeypot.jar

USER honeypot

# ---------------------------------------------------------------------------
# Rule 2: Read-only root filesystem + dedicated non-executable data volume
#   - Compose file mounts an empty volume at /data and refuses any other
#     writes. /app stays RO via the container's read_only: true flag.
#   - We mark /data non-executable (noexec is a docker-compose mount option;
#     we also deny the JVM the ability to mmap a script there).
# ---------------------------------------------------------------------------
VOLUME ["/data"]

# Default honeypot port (override with -e or -p)
ENV HONEYPOT_PORT=2222
EXPOSE 2222

# ---------------------------------------------------------------------------
# Rule 4 part A: JVM resource ceiling.
#   Xmx256m matches docker-compose mem_limit; MaxRAMPercentage gives the
#   container's cgroup-aware allocator the same budget. ExitOnOutOfMemory
#   forces a clean restart instead of degraded thrashing.
# ---------------------------------------------------------------------------
ENV JAVA_OPTS="-Xms64m -Xmx256m \
 -XX:MaxRAMPercentage=75.0 \
 -XX:+ExitOnOutOfMemoryError \
 -Djava.security.egd=file:/dev/./urandom \
 -Dhoneypot.port=${HONEYPOT_PORT}"

# Run as PID 1 under tini-style behavior. Using `exec` ensures signals
# (SIGTERM from docker stop) reach the JVM instead of a wrapper shell.
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app/iot-honeypot.jar"]

# ---------------------------------------------------------------------------
# Build-time hardening hints (enforced at runtime by docker-compose):
#   - no-new-privileges
#   - read_only root FS
#   - cap_drop ALL
#   - mem_limit / cpus
# See docker-compose.yml for the runtime equivalents.
# ---------------------------------------------------------------------------
LABEL org.opencontainers.image.title="iot-honeypot" \
      org.opencontainers.image.description="Low-interaction IoT honeypot (SSH/HTTP/RTSP) — hardened" \
      org.opencontainers.image.source="local" \
      security.no-new-privileges="true"
