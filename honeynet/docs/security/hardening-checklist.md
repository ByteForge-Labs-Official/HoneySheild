# Hardening Checklist

- [x] All honeypot containers run with non-root uid (10001) and `/sbin/nologin` shell.
- [x] `read_only: true`, tmpfs with `nosuid,nodev,noexec`.
- [x] `cap_drop: [ALL]`, `no-new-privileges`, seccomp=default.
- [x] CPU/MEM/PID cgroup limits per compose service.
- [x] Internal Docker network (`internal: true`) for honeypot subnet.
- [x] Host iptables egress block (`deploy/hardening/firewall/setup-firewall.sh`).
- [x] Host sysctl (`deploy/hardening/sysctl/10-honeypot.conf`).
- [x] SSH port relocated from 22 to 2200.
- [x] Traefik forwardauth protects admin endpoints.
- [x] All secrets in `.env`, never baked into images.
- [x] Postgres + Redis require passwords (no `trust`).
- [x] MQTT broker ACLs restrict to bridge user.
- [x] Suricata runs in `workers` mode with multi-thread pcap.
- [x] Elastic + Kibana require basic auth.
- [x] Brute-force login throttling (`fail2ban`-style in FastAPI).
- [x] Daily Postgres backup (`deploy/scripts/backup.sh`).
