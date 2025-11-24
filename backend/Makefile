# Backend Makefile for Docker image builds and deployments

# Color output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m

# Default image names (can be overridden)
IMAGE ?=
API_IMAGE ?= $(if $(IMAGE),$(IMAGE),notetaker-api:latest)
WORKER_IMAGE ?= $(if $(IMAGE),$(IMAGE),notetaker-worker:latest)

.PHONY: help
help: ## Show this help message
	@echo "$(GREEN)Backend Build Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

.PHONY: build-api
build-api: ## Build API Docker image
	@echo "$(GREEN)Building API image: $(API_IMAGE)$(NC)"
	@docker build --platform linux/amd64 -t $(API_IMAGE) -f Dockerfile .
	@echo "$(GREEN)✓ API image built$(NC)"

.PHONY: build-worker
build-worker: ## Build Worker Docker image
	@echo "$(GREEN)Building Worker image: $(WORKER_IMAGE)$(NC)"
	@docker build -t $(WORKER_IMAGE) -f Dockerfile.worker .
	@echo "$(GREEN)✓ Worker image built$(NC)"

.PHONY: build-all
build-all: build-api build-worker ## Build both API and Worker images
	@echo "$(GREEN)✓ All images built successfully$(NC)"

.PHONY: push-api
push-api: ## Push API image to registry
	@echo "$(GREEN)Pushing API image: $(API_IMAGE)$(NC)"
	@docker push $(API_IMAGE)
	@echo "$(GREEN)✓ API image pushed$(NC)"

.PHONY: push-worker
push-worker: ## Push Worker image to registry
	@echo "$(GREEN)Pushing Worker image: $(WORKER_IMAGE)$(NC)"
	@docker push $(WORKER_IMAGE)
	@echo "$(GREEN)✓ Worker image pushed$(NC)"

.PHONY: push-all
push-all: push-api push-worker ## Push both images to registry
	@echo "$(GREEN)✓ All images pushed successfully$(NC)"

.PHONY: test-local
test-local: ## Run tests locally
	@echo "$(GREEN)Running tests...$(NC)"
	@uv run pytest tests/ -v
	@echo "$(GREEN)✓ Tests passed$(NC)"

.PHONY: lint
lint: ## Run code linting
	@echo "$(GREEN)Running linters...$(NC)"
	@uv run ruff check app/
	@echo "$(GREEN)✓ Linting passed$(NC)"

.PHONY: format
format: ## Format code
	@echo "$(GREEN)Formatting code...$(NC)"
	@uv run ruff format app/
	@echo "$(GREEN)✓ Code formatted$(NC)"

.PHONY: run-api-local
run-api-local: ## Run API service locally
	@echo "$(GREEN)Starting API service locally...$(NC)"
	@uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: run-worker-local
run-worker-local: ## Run Worker service locally
	@echo "$(GREEN)Starting Worker service locally...$(NC)"
	@uv run uvicorn app.worker:app --reload --host 0.0.0.0 --port 8001

.PHONY: db-upgrade
db-upgrade: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	@uv run alembic upgrade head
	@echo "$(GREEN)✓ Database migrated$(NC)"

.PHONY: db-downgrade
db-downgrade: ## Rollback last database migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	@uv run alembic downgrade -1
	@echo "$(GREEN)✓ Migration rolled back$(NC)"

.PHONY: db-revision
db-revision: ## Create new database migration
	@read -p "Migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"
	@echo "$(GREEN)✓ Migration created$(NC)"

.PHONY: clean-docker
clean-docker: ## Clean up Docker images and containers
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	@docker system prune -f
	@echo "$(GREEN)✓ Docker cleaned$(NC)"

.PHONY: shell
shell: ## Open Python shell with app context
	@uv run python -i -c "from app.database import AsyncSessionLocal; from app.models import *; print('Database models loaded')"
