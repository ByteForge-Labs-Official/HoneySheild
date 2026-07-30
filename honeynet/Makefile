.PHONY: help up down logs ps restart build pull prune bootstrap backup restore \
        lint backend-test frontend-test openapi docs clean reset

SHELL := /bin/bash
COMPOSE_FILE := deploy/docker-compose.yml
ENV_FILE     := .env
DC := docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE)

help: ## list available targets
	@awk 'BEGIN {FS=":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## start the full stack
	$(DC) up -d --remove-orphans

down: ## stop and remove containers (keep volumes)
	$(DC) down --remove-orphans

logs: ## follow logs
	$(DC) logs -f --tail=200

ps:
	$(DC) ps

restart:
	$(DC) restart

build:
	$(DC) build --pull

pull:
	$(DC) pull

prune: ## ⚠ docker system prune
	docker system prune -af

bootstrap: ## first-time init: migrate + seed + import dashboards
	./deploy/scripts/bootstrap.sh

backup:
	./deploy/scripts/backup.sh

restore:
	@read -p "Backup file path: " f; ./deploy/scripts/restore.sh "$$f"

lint:
	cd backend && ruff check . && mypy app
	cd frontend && npm run lint

backend-test:
	cd backend && pytest -q

frontend-test:
	cd frontend && npm run test --silent

openapi: ## dump OpenAPI JSON to docs/api/openapi.json
	./deploy/scripts/openapi-dump.sh

docs:
	@echo "Open docs/architecture/00-overview.md"

clean: ## remove ephemeral logs / build cache
	rm -rf backend/.mypy_cache backend/.pytest_cache \
	       frontend/.vite frontend/node_modules/.cache

reset: down ## ⚠ nukes volumes
	docker volume rm $$(docker volume ls -q | grep honeynet) || true
