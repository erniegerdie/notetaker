# Notetaker GCP Deployment Makefile
# Root orchestrator for deploying to Google Cloud Platform

# Color output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

# GCP Configuration
PROJECT_ID ?= $(shell gcloud config get-value project)
REGION ?= $(shell gcloud config get-value compute/region 2>/dev/null || echo "europe-west1")
API_SERVICE_NAME = notetaker-api
WORKER_SERVICE_NAME = notetaker-worker
SQL_INSTANCE_NAME = notetaker-db
TASKS_QUEUE_NAME = video-processing-queue
IMAGE_TAG ?= latest

# Artifact Registry
REGISTRY = $(REGION)-docker.pkg.dev
REPOSITORY = notetaker
API_IMAGE = $(REGISTRY)/$(PROJECT_ID)/$(REPOSITORY)/$(API_SERVICE_NAME):$(IMAGE_TAG)
WORKER_IMAGE = $(REGISTRY)/$(PROJECT_ID)/$(REPOSITORY)/$(WORKER_SERVICE_NAME):$(IMAGE_TAG)

.PHONY: help
help: ## Show this help message
	@echo "$(GREEN)Notetaker GCP Deployment Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Quick Start:$(NC)"
	@echo "  1. make check-tools"
	@echo "  2. make setup-gcp"
	@echo "  3. make deploy-all"
	@echo ""

.PHONY: check-tools
check-tools: ## Verify required tools are installed
	@echo "$(GREEN)Checking required tools...$(NC)"
	@command -v gcloud >/dev/null 2>&1 || { echo "$(RED)gcloud CLI not installed$(NC)"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)docker not installed$(NC)"; exit 1; }
	@echo "$(GREEN)✓ All required tools installed$(NC)"

.PHONY: check-env
check-env: ## Verify environment variables are set
	@echo "$(GREEN)Checking environment variables...$(NC)"
	@test -n "$(PROJECT_ID)" || { echo "$(RED)GCP_PROJECT_ID not set$(NC)"; exit 1; }
	@echo "$(GREEN)✓ Project ID: $(PROJECT_ID)$(NC)"
	@echo "$(GREEN)✓ Region: $(REGION)$(NC)"

.PHONY: setup-gcp
setup-gcp: check-tools check-env ## Initial GCP setup (one-time)
	@echo "$(GREEN)Setting up GCP infrastructure...$(NC)"
	$(MAKE) -C infrastructure enable-apis
	$(MAKE) -C infrastructure create-artifact-registry
	$(MAKE) -C infrastructure create-sql
	$(MAKE) -C infrastructure create-tasks-queue
	$(MAKE) -C infrastructure setup-secrets
	@echo "$(GREEN)✓ GCP setup complete$(NC)"

.PHONY: build-all
build-all: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	$(MAKE) -C backend build-api IMAGE=$(API_IMAGE)
	$(MAKE) -C backend build-worker IMAGE=$(WORKER_IMAGE)
	@echo "$(GREEN)✓ All images built$(NC)"

.PHONY: push-all
push-all: ## Push all Docker images to Artifact Registry
	@echo "$(GREEN)Pushing Docker images...$(NC)"
	$(MAKE) -C backend push-api IMAGE=$(API_IMAGE)
	$(MAKE) -C backend push-worker IMAGE=$(WORKER_IMAGE)
	@echo "$(GREEN)✓ All images pushed$(NC)"

.PHONY: deploy-api
deploy-api: ## Deploy API service to Cloud Run
	@echo "$(GREEN)Deploying API service...$(NC)"
	@gcloud run deploy $(API_SERVICE_NAME) \
		--image $(API_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--memory 1Gi \
		--timeout 900 \
		--max-instances 10 \
		--add-cloudsql-instances $(PROJECT_ID):$(REGION):$(SQL_INSTANCE_NAME) \
		--set-secrets "\
DATABASE_URL=database-url:5,\
OPENAI_API_KEY=openai-api-key:latest,\
OPENROUTER_API_KEY=openrouter-api-key:latest,\
SUPABASE_URL=supabase-url:latest,\
SUPABASE_ANON_KEY=supabase-anon-key:latest,\
SUPABASE_JWT_SECRET=supabase-jwt-secret:latest,\
R2_ENDPOINT_URL=r2-endpoint-url:latest,\
R2_ACCESS_KEY_ID=r2-access-key-id:latest,\
R2_SECRET_ACCESS_KEY=r2-secret-access-key:latest,\
R2_BUCKET_NAME=r2-bucket-name:latest,\
R2_PUBLIC_URL=r2-public-url:latest,\
GCP_PROJECT_ID=gcp-project-id:latest,\
GCP_REGION=gcp-region:latest,\
CLOUD_TASKS_QUEUE=cloud-tasks-queue:latest,\
WORKER_SERVICE_URL=worker-service-url:latest,\
CLOUD_TASKS_SERVICE_ACCOUNT=cloud-tasks-service-account:latest"
	@echo "$(GREEN)✓ API service deployed$(NC)"

.PHONY: deploy-worker
deploy-worker: ## Deploy worker service to Cloud Run
	@echo "$(GREEN)Deploying worker service...$(NC)"
	@gcloud run deploy $(WORKER_SERVICE_NAME) \
		--image $(WORKER_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--no-allow-unauthenticated \
		--memory 2Gi \
		--cpu 2 \
		--timeout 3600 \
		--max-instances 5 \
		--cpu-boost \
		--add-cloudsql-instances $(PROJECT_ID):$(REGION):$(SQL_INSTANCE_NAME) \
		--set-secrets "\
DATABASE_URL=database-url:latest,\
OPENAI_API_KEY=openai-api-key:latest,\
OPENROUTER_API_KEY=openrouter-api-key:latest,\
R2_ENDPOINT_URL=r2-endpoint-url:latest,\
R2_ACCESS_KEY_ID=r2-access-key-id:latest,\
R2_SECRET_ACCESS_KEY=r2-secret-access-key:latest,\
R2_BUCKET_NAME=r2-bucket-name:latest,\
R2_PUBLIC_URL=r2-public-url:latest,\
GCP_PROJECT_ID=gcp-project-id:latest,\
GCP_REGION=gcp-region:latest"
	@echo "$(GREEN)✓ Worker service deployed$(NC)"

.PHONY: deploy-all
deploy-all: build-all push-all deploy-api deploy-worker ## Build, push, and deploy all services
	@echo "$(GREEN)✓ Complete deployment finished$(NC)"
	@echo ""
	@echo "$(YELLOW)API URL:$(NC)"
	@gcloud run services describe $(API_SERVICE_NAME) --region $(REGION) --format 'value(status.url)'
	@echo ""
	@echo "$(YELLOW)Worker URL:$(NC)"
	@gcloud run services describe $(WORKER_SERVICE_NAME) --region $(REGION) --format 'value(status.url)'

.PHONY: db-migrate
db-migrate: ## Run database migrations on Cloud SQL
	@echo "$(GREEN)Running database migrations...$(NC)"
	@echo "$(YELLOW)Starting Cloud SQL Proxy...$(NC)"
	@cloud-sql-proxy $(PROJECT_ID):$(REGION):$(SQL_INSTANCE_NAME) &
	@sleep 3
	@cd backend && uv run alembic upgrade head
	@pkill cloud-sql-proxy
	@echo "$(GREEN)✓ Migrations complete$(NC)"

.PHONY: logs-api
logs-api: ## Tail API service logs
	@gcloud run services logs tail $(API_SERVICE_NAME) --region $(REGION)

.PHONY: logs-worker
logs-worker: ## Tail worker service logs
	@gcloud run services logs tail $(WORKER_SERVICE_NAME) --region $(REGION)

.PHONY: status
status: ## Show deployment status
	@echo "$(GREEN)Deployment Status:$(NC)"
	@echo ""
	@echo "$(YELLOW)API Service:$(NC)"
	@gcloud run services describe $(API_SERVICE_NAME) --region $(REGION) --format 'table(status.conditions.type,status.conditions.status)' 2>/dev/null || echo "  Not deployed"
	@echo ""
	@echo "$(YELLOW)Worker Service:$(NC)"
	@gcloud run services describe $(WORKER_SERVICE_NAME) --region $(REGION) --format 'table(status.conditions.type,status.conditions.status)' 2>/dev/null || echo "  Not deployed"
	@echo ""
	@echo "$(YELLOW)Cloud SQL:$(NC)"
	@gcloud sql instances describe $(SQL_INSTANCE_NAME) --format 'value(state)' 2>/dev/null || echo "  Not created"
	@echo ""
	@echo "$(YELLOW)Cloud Tasks Queue:$(NC)"
	@gcloud tasks queues describe $(TASKS_QUEUE_NAME) --location $(REGION) --format 'value(state)' 2>/dev/null || echo "  Not created"

.PHONY: shell-api
shell-api: ## Connect to API service shell
	@gcloud run services proxy $(API_SERVICE_NAME) --region $(REGION)

.PHONY: rollback-api
rollback-api: ## Rollback API service to previous revision
	@echo "$(YELLOW)Rolling back API service...$(NC)"
	@gcloud run services update-traffic $(API_SERVICE_NAME) --region $(REGION) --to-revisions LATEST=0,PREVIOUS=100
	@echo "$(GREEN)✓ API service rolled back$(NC)"

.PHONY: rollback-worker
rollback-worker: ## Rollback worker service to previous revision
	@echo "$(YELLOW)Rolling back worker service...$(NC)"
	@gcloud run services update-traffic $(WORKER_SERVICE_NAME) --region $(REGION) --to-revisions LATEST=0,PREVIOUS=100
	@echo "$(GREEN)✓ Worker service rolled back$(NC)"

.PHONY: clean
clean: ## Clean up all GCP resources (DESTRUCTIVE)
	@echo "$(RED)WARNING: This will delete all GCP resources!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) -C infrastructure clean; \
	fi

.PHONY: cost-estimate
cost-estimate: ## Show estimated monthly costs
	@echo "$(GREEN)Estimated Monthly Costs:$(NC)"
	@echo ""
	@echo "  Cloud Run API:        ~$$0-2  (serverless, scales to zero)"
	@echo "  Cloud Run Worker:     ~$$2-5  (pay per execution)"
	@echo "  Cloud SQL (f1-micro): ~$$8    (always-on PostgreSQL)"
	@echo "  Cloud Tasks:          ~$$0    (free tier: 1M ops/month)"
	@echo "  Artifact Registry:    ~$$0-1  (storage)"
	@echo "  Secret Manager:       ~$$0    (6 secrets free)"
	@echo "  $(YELLOW)─────────────────────────────────$(NC)"
	@echo "  $(GREEN)Total:                ~$$10-16/month$(NC)"
	@echo ""
	@echo "  Compare to Render + Celery: ~$$28/month"
	@echo "  $(GREEN)Savings: ~$$12-18/month (~60%)$(NC)"
