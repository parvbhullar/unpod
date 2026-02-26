PYTHON_VERSION ?= 3.12
IMAGE_TAG ?= latest
IMAGE_NAME ?= voice-executor
EXECUTOR := super_services/orchestration/executors/voice_executor_v3.py

# Detect uv; auto-install if missing (works on macOS + Linux)
UV := $(shell command -v uv 2>/dev/null)
ifndef UV
  $(info uv not found — installing via astral.sh...)
  UV_INSTALL := $(shell curl -LsSf https://astral.sh/uv/install.sh | sh >&2 2>&1)
  UV := $(or $(shell command -v uv 2>/dev/null),$(HOME)/.local/bin/uv)
endif

SERVICE_NAME := voice_lk_executor_v3
SERVICE_FILE := deployment/services/$(SERVICE_NAME).service

PREFECT_DIR := super_services/prefect_setup
DEPLOYMENTS := super_services/orchestration/task/deployments/task_deployments.py
TASK_DOCKERFILE := super_services/orchestration/task/deployments/Dockerfile
CEREBRIUM_DIR := deployment/cerebrium

.PHONY: build run setup local validate health test deploy-service \
        prefect-up prefect-down prefect-deploy prefect-refresh prefect-remote \
        k8s-qa k8s-prod k8s-prefect-qa k8s-prefect-prod \
        cerebrium-deploy cerebrium-logs

## Docker

build:  ## Build Docker image
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) .

run: build  ## Build + run Docker container
	docker run --rm --env-file .env $(IMAGE_NAME):$(IMAGE_TAG) start

## Local

setup:  ## Install deps + configure .env (interactive)
	$(UV) sync
	$(UV) run python $(EXECUTOR) setup

local:  ## Run locally in dev mode
	$(UV) run python $(EXECUTOR) dev

validate:  ## Check required env vars
	$(UV) run python $(EXECUTOR) validate-env

health:  ## Check service connectivity
	$(UV) run python $(EXECUTOR) health

test:  ## Run voice agent test suite
	./scripts/test_voice_agent_suite.sh

## Systemd (Linux)

deploy-service:  ## Deploy systemd service (run make setup first)
	@test -f .env || { echo "Error: .env not found. Run 'make setup' first."; exit 1; }
	sed 's|WorkingDirectory=.*|WorkingDirectory=$(CURDIR)|' $(SERVICE_FILE) \
		| sudo tee /etc/systemd/system/$(SERVICE_NAME).service > /dev/null
	sudo systemctl daemon-reload
	sudo systemctl enable $(SERVICE_NAME)
	sudo systemctl restart $(SERVICE_NAME)
	@echo "Service deployed from $(CURDIR)"
	@echo "Check status: sudo systemctl status $(SERVICE_NAME)"

## Prefect

prefect-up:  ## Start Prefect server + worker (local)
	docker compose -f $(PREFECT_DIR)/local/docker-compose-local-base.yaml down --remove-orphans
	docker compose -f $(PREFECT_DIR)/local/docker-compose-local-base.yaml up -d
	docker compose -f $(PREFECT_DIR)/local/docker-call-worker-compose.yaml down --remove-orphans
	docker compose -f $(PREFECT_DIR)/local/docker-call-worker-compose.yaml up -d
	@echo "Prefect server: http://localhost:4200"

prefect-down:  ## Stop Prefect server + worker (local)
	docker compose -f $(PREFECT_DIR)/local/docker-call-worker-compose.yaml down --remove-orphans
	docker compose -f $(PREFECT_DIR)/local/docker-compose-local-base.yaml down --remove-orphans

prefect-deploy:  ## Register Prefect flow deployments
	$(UV) run python $(DEPLOYMENTS)

prefect-refresh:  ## Sync deps + rebuild task image + re-register deployments
	$(UV) sync
	docker build -t call-task:local -f $(TASK_DOCKERFILE) .
	$(UV) run python $(DEPLOYMENTS)
	@echo "Prefect deployments refreshed."

prefect-remote:  ## Start Prefect for qa/prod (ENV=qa|prod)
	@test -n "$(ENV)" || { echo "Usage: make prefect-remote ENV=qa|prod"; exit 1; }
	docker compose -f $(PREFECT_DIR)/$(ENV)/docker-compose-$(ENV).yaml down --remove-orphans
	docker compose -f $(PREFECT_DIR)/$(ENV)/docker-compose-$(ENV).yaml up -d
	docker compose -f $(PREFECT_DIR)/$(ENV)/docker-call-worker-compose.yaml down --remove-orphans
	docker compose -f $(PREFECT_DIR)/$(ENV)/docker-call-worker-compose.yaml up -d
	$(UV) run python $(DEPLOYMENTS)
	@echo "Prefect $(ENV) started."

## Kubernetes

k8s-qa:  ## Deploy all to K8s QA (executor + Prefect)
	kubectl apply -k deployment/k8s/overlays/qa/

k8s-prod:  ## Deploy all to K8s Prod (executor + Prefect)
	kubectl apply -k deployment/k8s/overlays/prod/

k8s-prefect-qa:  ## Deploy only Prefect to K8s QA
	kubectl apply -k deployment/k8s/base/prefect/

k8s-prefect-prod:  ## Deploy only Prefect to K8s Prod
	kubectl apply -k deployment/k8s/base/prefect/

## Cerebrium

cerebrium-deploy:  ## Deploy to Cerebrium cloud
	$(UV) run cerebrium deploy --config-file $(CEREBRIUM_DIR)/cerebrium.toml

cerebrium-logs:  ## View Cerebrium deployment logs
	$(UV) run cerebrium logs unpod-voice-agent

## Help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'
