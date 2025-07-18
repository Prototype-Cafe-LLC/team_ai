.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: dev-build
dev-build: ## Build all Docker containers for development
	docker compose build

.PHONY: dev
dev: ## Start development environment
	docker compose up

.PHONY: dev-detached
dev-detached: ## Start development environment in detached mode
	docker compose up -d

.PHONY: stop
stop: ## Stop all containers
	docker compose stop

.PHONY: down
down: ## Stop and remove all containers
	docker compose down

.PHONY: clean
clean: ## Clean all containers, volumes, and images
	docker compose down -v --rmi local

.PHONY: logs
logs: ## Show logs from all containers
	docker compose logs -f

.PHONY: logs-backend
logs-backend: ## Show backend logs
	docker compose logs -f backend

.PHONY: logs-frontend
logs-frontend: ## Show frontend logs
	docker compose logs -f frontend

.PHONY: shell-backend
shell-backend: ## Open shell in backend container
	docker compose exec backend bash

.PHONY: shell-frontend
shell-frontend: ## Open shell in frontend container
	docker compose exec frontend sh

.PHONY: db-shell
db-shell: ## Open PostgreSQL shell
	docker compose exec postgres psql -U postgres -d multiagent

.PHONY: redis-cli
redis-cli: ## Open Redis CLI
	docker compose exec redis redis-cli

.PHONY: test-backend
test-backend: ## Run backend tests
	docker compose exec backend pytest

.PHONY: test-frontend
test-frontend: ## Run frontend tests
	docker compose exec frontend npm test

.PHONY: format-backend
format-backend: ## Format backend code
	docker compose exec backend black .
	docker compose exec backend isort .

.PHONY: lint-backend
lint-backend: ## Lint backend code
	docker compose exec backend flake8
	docker compose exec backend mypy app

.PHONY: migrate
migrate: ## Run database migrations
	docker compose exec backend alembic upgrade head

.PHONY: migrate-create
migrate-create: ## Create a new migration
	@read -p "Enter migration name: " name; \
	docker compose exec backend alembic revision --autogenerate -m "$$name"

.PHONY: install-deps
install-deps: ## Install dependencies
	cd frontend && npm install
	cd backend && pip install -r requirements.txt