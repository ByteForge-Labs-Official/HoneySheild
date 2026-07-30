# Runbook — Incident Response

## An attacker appears to have escaped the honeypot

1. **Contain.**  The container is on `internal: true`, so the blast radius is the
   honeypot subnet.  Pause the container: `docker compose pause honeypot-ssh`.
2. **Snapshot the host.**  `./deploy/scripts/forensic-snapshot.sh > incident-$(date -u +%s).tar`.
3. **Rotate.**  Re-deploy the affected honeypot with a fresh image; pull any new
   rules from the AI service (`POST /api/v1/threats/feedback`).
4. **Post-mortem.**  Open a GitHub issue tagged `incident`, attach the snapshot
   and the matching `events` rows.

## Disk fills up

1. `du -sh data/*` to find the culprit (almost always `data/pcap`).
2. `find data/pcap -type f -mtime +14 -delete` (or use Suricata's
   `output.rotate` / Zeek's log rotation).
3. `make restart` to clear stale container state.

## Elasticsearch is yellow/red

```bash
docker compose exec elasticsearch \
  curl -s localhost:9200/_cluster/health?pretty
docker compose exec elasticsearch \
  curl -s -XPOST localhost:9200/_cluster/reroute?retry_failed=true
```

If indices are read-only due to disk watermark, run
`./deploy/scripts/es-free-disk.sh` (raises the watermark temporarily and rotates
old indices, then restores it).
