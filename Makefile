# =============================================================================
# Unpod - Development Commands
# =============================================================================
# Usage:
#   make quick-start   # One command to set up everything
#   make dev           # Start development servers
#   make stop          # Stop Docker containers
#   make clean         # Stop containers and remove data
#   make help          # Show all commands
# =============================================================================

.PHONY: help quick-start setup env deps docker db migrate dev stop clean logs status

DOCKER_COMPOSE = docker compose -f docker-compose.simple.yml
BACKEND_DIR = apps/backend-core
VENV = $(BACKEND_DIR)/.venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

help: ## Show this help
	@echo "Unpod Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# Quick Start
# =============================================================================

quick-start: env deps docker db migrate ## Full setup in one command
	@echo ""
	@echo "============================================"
	@echo "  Setup complete!"
	@echo "============================================"
	@echo ""
	@echo "  Run 'make dev' to start development"
	@echo ""
	@echo "  Access:"
	@echo "    Frontend:    http://localhost:3000"
	@echo "    Backend API: http://localhost:8000"
	@echo "    Admin Panel: http://localhost:8000/unpod-admin/"
	@echo ""

setup: env deps ## Install dependencies only (no Docker)

# =============================================================================
# Individual Steps
# =============================================================================

env: ## Copy environment files if they don't exist
	@test -f $(BACKEND_DIR)/.env.local || (cp $(BACKEND_DIR)/.env.docker $(BACKEND_DIR)/.env.local && echo "Created $(BACKEND_DIR)/.env.local")
	@test -f apps/web/.env.local || (test -f apps/web/.env.local.example && cp apps/web/.env.local.example apps/web/.env.local && echo "Created apps/web/.env.local") || true

deps: ## Install npm + Python dependencies
	@echo "Installing npm dependencies..."
	@npm install --silent 2>&1 | tail -1
	@echo "Setting up Python virtual environment..."
	@test -d $(VENV) || python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip --quiet
	@$(PIP) install -r $(BACKEND_DIR)/requirements/local.txt --quiet
	@echo "Dependencies installed."

docker: ## Start Docker containers (PostgreSQL, MongoDB, Redis)
	$(DOCKER_COMPOSE) up -d

db: ## Wait for databases to be healthy
	@echo "Waiting for databases..."
	@until docker exec unpod-postgres pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done
	@echo "  PostgreSQL: ready"
	@until docker exec unpod-mongodb mongosh --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; do sleep 1; done
	@echo "  MongoDB: ready"
	@until docker exec unpod-redis redis-cli ping >/dev/null 2>&1; do sleep 1; done
	@echo "  Redis: ready"

migrate: ## Run Django migrations
	cd $(BACKEND_DIR) && $(PYTHON) manage.py migrate --no-input

# =============================================================================
# Development
# =============================================================================

dev: ## Start frontend + backend dev servers
	npm run dev

dev-backend: ## Start backend only (Django)
	cd $(BACKEND_DIR) && $(PYTHON) manage.py runserver

dev-frontend: ## Start frontend only (Next.js)
	npx nx dev web

# =============================================================================
# Maintenance
# =============================================================================

stop: ## Stop Docker containers
	$(DOCKER_COMPOSE) down

clean: ## Stop containers and remove all data volumes
	$(DOCKER_COMPOSE) down -v

logs: ## Tail Docker container logs
	$(DOCKER_COMPOSE) logs -f

status: ## Show status of Docker containers
	$(DOCKER_COMPOSE) ps

superuser: ## Create Django superuser
	cd $(BACKEND_DIR) && $(PYTHON) manage.py createsuperuser
