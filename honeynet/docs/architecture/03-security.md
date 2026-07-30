# Security Architecture

## Layered defenses

| Layer | Mechanism |
|---|---|
| 1. Process | Honeypot containers run as uid 10001, `nologin` shell, no capabilities |
| 2. Filesystem | `read_only: true` + tmpfs `/tmp` + tmpfs `/run` |
| 3. Network    | `internal: true` Docker network + iptables egress block + uid-owner filter |
| 4. App       | `Sanitizer.cleanLine()` (max 1024), parameterized SQL, no native exec |
| 5. Storage   | `input sanitisers` + bounded VARCHAR in all DB columns |
| 6. OS        | sysctl: `net.ipv4.tcp_syncookies=1`, `rp_filter=1`, `kernel.randomize_va_space=2` |

## Mandatory controls (every honeypot container)

```yaml
security_opt:
  - no-new-privileges:true
  - seccomp:default
cap_drop: [ALL]
read_only: true
tmpfs:
  - /tmp:rw,nosuid,nodev,noexec,size=64m
  - /run:rw,nosuid,nodev,noexec,size=16m
ulimits:
  nofile: { soft: 512, hard: 1024 }
  nproc:  { soft:  64, hard:  128 }
deploy:
  resources:
    limits:
      cpus: "0.50"
      memory: 256M
      pids: 256
```

## Threat model

See [`docs/security/threat-model.md`](../security/threat-model.md).

## Operator access

* Multi-factor admin login backed by JWT (HS256, 60-min access, 7-day refresh).
* Role-based authorization: `viewer`, `analyst`, `admin`.
* All admin actions audit-logged to `audit_log` (append-only).
* Optional IP allow-list via Traefik `forwardauth` middleware.
