# Runbook — Bootstrap

```bash
# 0. Pre-flight
docker --version          # 24+
docker compose version    # v2.20+
openssl version

# 1. Configure secrets
cp .env.example .env
$EDITOR .env                       # change every "changeme-..."

# 2. Bring the stack up (postgres, redis, mqtt, ids, app, ui)
docker compose -f deploy/docker-compose.yml --env-file .env pull
docker compose -f deploy/docker-compose.yml --env-file .env up -d

# 3. Run first-time migrations + seed
./deploy/scripts/bootstrap.sh

# 4. Smoke-test
curl -fsS http://localhost:8000/api/v1/health | jq
curl -fsS http://localhost/ | head -n1
ssh -p "${HONEYPOT_PUBLIC_SSH_PORT:-2222}" -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null root@localhost   # expect shell banner
```
