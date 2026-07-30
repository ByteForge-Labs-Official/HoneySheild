# Runbook — Backup & Restore

## Postgres

```bash
# Backup (full pg_dump, custom-format, gzipped)
./deploy/scripts/backup.sh

# Restore
./deploy/scripts/restore.sh backups/honeynet-YYYYMMDD-HHMM.dump.gz
```

## Elasticsearch indices

```bash
# Snapshot repository (one-time)
curl -XPUT :9200/_snapshot/honeynet \
  -H 'content-type: application/json' \
  -d '{"type":"fs","settings":{"location":"/usr/share/elasticsearch/snap"}}'

# Snapshot
curl -XPUT :9200/_snapshot/honeynet/snap-$(date -u +%Y%m%dT%H%M%SZ)?wait_for_completion=false

# Restore
curl -XPOST :9200/_snapshot/honeynet/snap-XXX/_restore \
  -H 'content-type: application/json' -d '{"include_global_state":false}'
```

## Redis

* `appendonly yes`, snapshot every 60 s if ≥ 1 key changed (`save 60 1`).
* Backups live in `data/redis/dump.rdb`; bind-mounted so a host-side `cp` is
  sufficient.
