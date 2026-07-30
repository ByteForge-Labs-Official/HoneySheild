# Threat Model

## Out of scope

* Physical access to the host or Docker socket.
* Compromise of the host kernel or hypervisor.

## In scope

| Threat | Vector | Mitigation |
|---|---|---|
| Container escape | RCE in a bait service | `cap_drop:[ALL]`, `no-new-privileges`, AppArmor, seccomp, egress block, read-only FS |
| Lateral movement | foothold → other services | subnet segmentation + iptables host isolation |
| Log injection | control chars in attacker input | `Sanitizer.cleanLine()` (≤1024 chars, strip ANSI/C0/C1) |
| SQL injection | native logs concatenated into queries | SQLAlchemy Core / parameterized statements only |
| DoS / resource exhaustion | infinite loops, large payloads | bounded readers, idle timeouts, per-IP rate limits, container cgroup limits |
| Token theft | leaked `.env` | per-deploy rotation, JWT short TTL, env file outside image |
| Data exfiltration | DNS / outbound HTTP | DNS NXDOMAIN via dnsmasq sinkhole; OUTPUT chain uid-filter blocks all egress |
| Supply chain | malicious base image | pinned digests, Trivy scan in CI, `cosign` verify |

## MITRE ATT&CK coverage

Honeypots are designed to detect and characterize:
`TA0001 Initial Access`, `TA0007 Discovery`, `TA0011 C&C`, and parts of
`TA0008 Lateral Movement` (when probing other honeypot ports).

The AI service tags every captured event with the relevant techniques; see the
`mitre_tags` dashboard for coverage heat-map.
