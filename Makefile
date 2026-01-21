DOCKER_COMPOSE := docker compose

up:
	$(DOCKER_COMPOSE) up -d --build

up-dev:
	$(DOCKER_COMPOSE) up -d --build -f docker-compose.yml

up-prod:
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d --build

down:
	$(DOCKER_COMPOSE) down

down-prod:
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml down

logs:
	$(DOCKER_COMPOSE) logs -f

logs-prod:
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml logs -f

pull-models:
	$(DOCKER_COMPOSE) run --rm ollama ollama pull mxbai-embed-large && \
	$(DOCKER_COMPOSE) run --rm ollama ollama pull llama3.1:8b-instruct

ingest-test:
	$(DOCKER_COMPOSE) run --rm api python -m nexus.ingest.pipeline --collection test

ingest-dev:
	$(DOCKER_COMPOSE) run --rm api python -m nexus.ingest.pipeline --collection dev

ingest-library:
	$(DOCKER_COMPOSE) run --rm api python -m nexus.ingest.pipeline --collection library

eval:
	$(DOCKER_COMPOSE) run --rm api python -m nexus.eval.inspect_suite

backup:
	$(DOCKER_COMPOSE) exec db pg_dump -U nexus -d nexus > backup_$$(date +%Y%m%d_%H%M%S).sql

restore:
	$(DOCKER_COMPOSE) exec -T db psql -U nexus -d nexus < backup.sql

ps:
	$(DOCKER_COMPOSE) ps

stats:
	$(DOCKER_COMPOSE) stats

doctor:
	@echo "Checking Docker availability..."
	@docker info >/dev/null 2>&1 || (echo "Docker is not running or not accessible" && exit 1)
	@docker compose version
	@echo "Docker socket: $$DOCKER_HOST"

test-e2e:
	docker run --rm -v "$(PWD)/web:/work" -w /work mcr.microsoft.com/playwright:v1.57.0-jammy bash -lc "npm ci && npx playwright test"

# GPU support
up-gpu:
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.gpu.yml up -d --build

# Production deployment
deploy: up-prod
	@echo "Deployment complete!"
	@echo "Web: http://localhost:3000"
	@echo "API: http://localhost:8000"
	@echo "Ollama: http://localhost:11434"

# Stop all services
stop:
	$(DOCKER_COMPOSE) down --remove-orphans

# Clean up all volumes (WARNING: destroys data)
clean: down
	$(DOCKER_COMPOSE) down -v --remove-orphans
