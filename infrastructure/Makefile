# Infrastructure Makefile for GCP resource management

# Color output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m

# GCP Configuration
PROJECT_ID ?= $(shell gcloud config get-value project)
REGION ?= $(shell gcloud config get-value compute/region 2>/dev/null || echo "europe-west1")
SQL_INSTANCE_NAME = notetaker-db
SQL_DATABASE_NAME = notetaker
TASKS_QUEUE_NAME = video-processing-queue
REPOSITORY_NAME = notetaker

# Worker Configuration
WORKER_IMAGE_NAME = worker
WORKER_IMAGE_TAG ?= latest
WORKER_IMAGE_FULL = $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPOSITORY_NAME)/$(WORKER_IMAGE_NAME):$(WORKER_IMAGE_TAG)
WORKER_CPU ?= 4
WORKER_MEMORY ?= 8Gi
WORKER_TIMEOUT ?= 3600s
WORKER_MAX_INSTANCES ?= 10

.PHONY: help
help: ## Show this help message
	@echo "$(GREEN)Infrastructure Management Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Secrets Setup:$(NC)"
	@echo "  1. Copy template:  cp .env.prod.example .env.prod"
	@echo "  2. Edit values:    nano .env.prod"
	@echo "  3. Upload secrets: make setup-secrets"

.PHONY: check-project
check-project:
	@test -n "$(PROJECT_ID)" || { echo "$(RED)GCP_PROJECT_ID not set. Run: gcloud config set project PROJECT_ID$(NC)"; exit 1; }

.PHONY: enable-apis
enable-apis: check-project ## Enable required GCP APIs
	@echo "$(GREEN)Enabling GCP APIs...$(NC)"
	@gcloud services enable \
		run.googleapis.com \
		sqladmin.googleapis.com \
		cloudtasks.googleapis.com \
		artifactregistry.googleapis.com \
		secretmanager.googleapis.com \
		cloudbuild.googleapis.com \
		--project=$(PROJECT_ID)
	@echo "$(GREEN)✓ APIs enabled$(NC)"

.PHONY: create-artifact-registry
create-artifact-registry: check-project ## Create Artifact Registry repository
	@echo "$(GREEN)Creating Artifact Registry repository...$(NC)"
	@gcloud artifacts repositories create $(REPOSITORY_NAME) \
		--repository-format=docker \
		--location=$(REGION) \
		--description="Notetaker Docker images" \
		--project=$(PROJECT_ID) 2>/dev/null || echo "$(YELLOW)Repository already exists$(NC)"
	@echo "$(GREEN)✓ Artifact Registry ready$(NC)"
	@echo "$(YELLOW)Configure Docker:$(NC) gcloud auth configure-docker $(REGION)-docker.pkg.dev"

.PHONY: create-sql
create-sql: check-project ## Create Cloud SQL PostgreSQL instance
	@echo "$(GREEN)Creating Cloud SQL instance (this takes ~10 minutes)...$(NC)"
	@gcloud sql instances create $(SQL_INSTANCE_NAME) \
		--database-version=POSTGRES_15 \
		--tier=db-f1-micro \
		--region=$(REGION) \
		--database-flags=max_connections=100 \
		--storage-type=SSD \
		--storage-size=10GB \
		--backup-start-time=03:00 \
		--maintenance-window-day=SUN \
		--maintenance-window-hour=04 \
		--project=$(PROJECT_ID) 2>/dev/null || echo "$(YELLOW)Instance already exists$(NC)"
	@echo "$(GREEN)Creating database...$(NC)"
	@gcloud sql databases create $(SQL_DATABASE_NAME) \
		--instance=$(SQL_INSTANCE_NAME) \
		--project=$(PROJECT_ID) 2>/dev/null || echo "$(YELLOW)Database already exists$(NC)"
	@echo "$(GREEN)✓ Cloud SQL instance ready$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "1. Set root password: $(GREEN)make set-sql-password$(NC)"
	@echo ""
	@echo "2. Add this DATABASE_URL to infrastructure/.env.prod:"
	@echo "   $(GREEN)DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@/$(SQL_DATABASE_NAME)?host=/cloudsql/$(PROJECT_ID):$(REGION):$(SQL_INSTANCE_NAME)$(NC)"
	@echo ""

.PHONY: set-sql-password
set-sql-password: check-project ## Set Cloud SQL root password
	@read -sp "Enter PostgreSQL password: " pwd; \
	echo; \
	gcloud sql users set-password postgres \
		--instance=$(SQL_INSTANCE_NAME) \
		--password=$$pwd \
		--project=$(PROJECT_ID)
	@echo "$(GREEN)✓ Password set$(NC)"

.PHONY: create-tasks-queue
create-tasks-queue: check-project ## Create Cloud Tasks queue
	@echo "$(GREEN)Creating Cloud Tasks queue...$(NC)"
	@gcloud tasks queues create $(TASKS_QUEUE_NAME) \
		--location=$(REGION) \
		--max-concurrent-dispatches=5 \
		--max-dispatches-per-second=5 \
		--max-attempts=3 \
		--min-backoff=60s \
		--max-backoff=3600s \
		--project=$(PROJECT_ID) 2>/dev/null || echo "$(YELLOW)Queue already exists$(NC)"
	@echo "$(GREEN)✓ Cloud Tasks queue ready$(NC)"

.PHONY: setup-secrets
setup-secrets: check-project ## Set up Secret Manager secrets from .env.prod
	@echo "$(GREEN)Setting up Secret Manager secrets from .env.prod...$(NC)"
	@test -f .env.prod || { echo "$(RED)Error: .env.prod not found. Copy .env.prod.example and fill in values.$(NC)"; exit 1; }
	@echo "$(YELLOW)Loading secrets from .env.prod...$(NC)"
	@set -a && . ./.env.prod && set +a && \
	$(MAKE) create-secret-from-env NAME=database-url VALUE='$$DATABASE_URL' && \
	$(MAKE) create-secret-from-env NAME=openai-api-key VALUE="$$OPENAI_API_KEY" && \
	$(MAKE) create-secret-from-env NAME=openrouter-api-key VALUE="$$OPENROUTER_API_KEY" && \
	$(MAKE) create-secret-from-env NAME=supabase-url VALUE="$$SUPABASE_URL" && \
	$(MAKE) create-secret-from-env NAME=supabase-anon-key VALUE="$$SUPABASE_ANON_KEY" && \
	$(MAKE) create-secret-from-env NAME=supabase-jwt-secret VALUE="$$SUPABASE_JWT_SECRET" && \
	$(MAKE) create-secret-from-env NAME=r2-endpoint-url VALUE="$$R2_ENDPOINT_URL" && \
	$(MAKE) create-secret-from-env NAME=r2-access-key-id VALUE="$$R2_ACCESS_KEY_ID" && \
	$(MAKE) create-secret-from-env NAME=r2-secret-access-key VALUE="$$R2_SECRET_ACCESS_KEY" && \
	$(MAKE) create-secret-from-env NAME=r2-bucket-name VALUE="$$R2_BUCKET_NAME" && \
	$(MAKE) create-secret-from-env NAME=r2-public-url VALUE="$$R2_PUBLIC_URL" && \
	$(MAKE) create-secret-from-env NAME=gcp-project-id VALUE="$$GCP_PROJECT_ID" && \
	$(MAKE) create-secret-from-env NAME=gcp-region VALUE="$$GCP_REGION" && \
	$(MAKE) create-secret-from-env NAME=cloud-tasks-queue VALUE="$$CLOUD_TASKS_QUEUE" && \
	$(MAKE) create-secret-from-env NAME=worker-service-url VALUE="$$WORKER_SERVICE_URL" && \
	$(MAKE) create-secret-from-env NAME=cloud-tasks-service-account VALUE="$$CLOUD_TASKS_SERVICE_ACCOUNT"
	@echo "$(GREEN)✓ All secrets configured from .env.prod$(NC)"

.PHONY: setup-secrets-interactive
setup-secrets-interactive: check-project ## Set up Secret Manager secrets interactively
	@echo "$(GREEN)Setting up Secret Manager secrets (interactive mode)...$(NC)"
	@echo "$(YELLOW)Enter secrets when prompted (or press Ctrl+C to skip):$(NC)"
	@echo ""
	@$(MAKE) create-secret NAME=database-url DESCRIPTION="PostgreSQL connection string (postgresql+asyncpg://user:pass@/db?host=/cloudsql/...)"
	@$(MAKE) create-secret NAME=openai-api-key DESCRIPTION="OpenAI API key"
	@$(MAKE) create-secret NAME=openrouter-api-key DESCRIPTION="OpenRouter API key"
	@$(MAKE) create-secret NAME=supabase-url DESCRIPTION="Supabase project URL"
	@$(MAKE) create-secret NAME=supabase-anon-key DESCRIPTION="Supabase anon key"
	@$(MAKE) create-secret NAME=supabase-jwt-secret DESCRIPTION="Supabase JWT secret"
	@$(MAKE) create-secret NAME=r2-endpoint-url DESCRIPTION="Cloudflare R2 endpoint URL"
	@$(MAKE) create-secret NAME=r2-access-key-id DESCRIPTION="Cloudflare R2 access key ID"
	@$(MAKE) create-secret NAME=r2-secret-access-key DESCRIPTION="Cloudflare R2 secret access key"
	@$(MAKE) create-secret NAME=r2-bucket-name DESCRIPTION="Cloudflare R2 bucket name"
	@$(MAKE) create-secret NAME=r2-public-url DESCRIPTION="Cloudflare R2 public URL (optional)"
	@$(MAKE) create-secret NAME=gcp-project-id DESCRIPTION="GCP Project ID"
	@$(MAKE) create-secret NAME=gcp-region DESCRIPTION="GCP Region (us-central1)"
	@$(MAKE) create-secret NAME=cloud-tasks-queue DESCRIPTION="Cloud Tasks queue name"
	@$(MAKE) create-secret NAME=worker-service-url DESCRIPTION="Worker Cloud Run service URL (set after first deploy)"
	@$(MAKE) create-secret NAME=cloud-tasks-service-account DESCRIPTION="Cloud Tasks service account email"
	@echo "$(GREEN)✓ Secrets configured$(NC)"

.PHONY: create-secret-from-env
create-secret-from-env: check-project
	@if [ -z '$(VALUE)' ]; then \
		echo "$(YELLOW)Skipping $(NAME) (empty value)$(NC)"; \
	else \
		gcloud secrets create $(NAME) \
			--replication-policy="automatic" \
			--project=$(PROJECT_ID) 2>/dev/null || echo "$(YELLOW)Secret $(NAME) already exists, updating...$(NC)"; \
		printf '%s' '$(VALUE)' | gcloud secrets versions add $(NAME) --data-file=- --project=$(PROJECT_ID); \
		echo "$(GREEN)✓ $(NAME)$(NC)"; \
	fi
	# IMPORTANT: Use single quotes around VALUE to prevent shell expansion of $ characters.
	# Use 'printf' instead of 'echo' to avoid trailing newlines.

.PHONY: create-secret
create-secret: check-project
	@gcloud secrets create $(NAME) \
		--replication-policy="automatic" \
		--project=$(PROJECT_ID) 2>/dev/null || echo "$(YELLOW)Secret $(NAME) already exists$(NC)"
	@echo "Enter value for $(NAME) ($(DESCRIPTION)):"
	@read -s value; \
	printf '%s' "$$value" | gcloud secrets versions add $(NAME) --data-file=- --project=$(PROJECT_ID)
	# IMPORTANT: Use 'printf' to avoid trailing newlines in secrets.

.PHONY: list-secrets
list-secrets: check-project ## List all secrets
	@echo "$(GREEN)Configured secrets:$(NC)"
	@gcloud secrets list --project=$(PROJECT_ID)

.PHONY: get-worker-url
get-worker-url: check-project ## Get worker service URL and update .env.prod
	@./get-worker-url.sh

.PHONY: grant-worker-permissions
grant-worker-permissions: check-project ## Grant Cloud Run worker permissions
	@echo "$(GREEN)Granting Cloud Tasks permissions to invoke worker...$(NC)"
	@PROJECT_NUMBER=$$(gcloud projects describe $(PROJECT_ID) --format="value(projectNumber)"); \
	gcloud run services add-iam-policy-binding notetaker-worker \
		--region=$(REGION) \
		--member=serviceAccount:service-$$PROJECT_NUMBER@gcp-sa-cloudtasks.iam.gserviceaccount.com \
		--role=roles/run.invoker \
		--project=$(PROJECT_ID)
	@echo "$(GREEN)✓ Permissions granted$(NC)"

.PHONY: status
status: check-project ## Show infrastructure status
	@echo "$(GREEN)Infrastructure Status:$(NC)"
	@echo ""
	@echo "$(YELLOW)Cloud SQL Instance:$(NC)"
	@gcloud sql instances describe $(SQL_INSTANCE_NAME) --format="table(state,databaseVersion,settings.tier)" --project=$(PROJECT_ID) 2>/dev/null || echo "  Not created"
	@echo ""
	@echo "$(YELLOW)Cloud Tasks Queue:$(NC)"
	@gcloud tasks queues describe $(TASKS_QUEUE_NAME) --location=$(REGION) --format="table(state,rateLimits.maxConcurrentDispatches)" --project=$(PROJECT_ID) 2>/dev/null || echo "  Not created"
	@echo ""
	@echo "$(YELLOW)Artifact Registry:$(NC)"
	@gcloud artifacts repositories describe $(REPOSITORY_NAME) --location=$(REGION) --format="table(name,format)" --project=$(PROJECT_ID) 2>/dev/null || echo "  Not created"
	@echo ""
	@echo "$(YELLOW)Secrets:$(NC)"
	@gcloud secrets list --format="table(name)" --project=$(PROJECT_ID) 2>/dev/null || echo "  None created"

.PHONY: clean
clean: check-project ## Delete all GCP resources (DESTRUCTIVE)
	@echo "$(RED)WARNING: This will DELETE all infrastructure resources!$(NC)"
	@echo "$(RED)This includes:$(NC)"
	@echo "  - Cloud SQL instance (all data will be lost)"
	@echo "  - Cloud Tasks queue"
	@echo "  - Artifact Registry repository"
	@echo "  - Secret Manager secrets"
	@echo ""
	@read -p "Type 'DELETE' to confirm: " confirm; \
	if [ "$$confirm" = "DELETE" ]; then \
		echo "$(YELLOW)Deleting Cloud SQL instance...$(NC)"; \
		gcloud sql instances delete $(SQL_INSTANCE_NAME) --project=$(PROJECT_ID) --quiet 2>/dev/null || true; \
		echo "$(YELLOW)Deleting Cloud Tasks queue...$(NC)"; \
		gcloud tasks queues delete $(TASKS_QUEUE_NAME) --location=$(REGION) --project=$(PROJECT_ID) --quiet 2>/dev/null || true; \
		echo "$(YELLOW)Deleting Artifact Registry...$(NC)"; \
		gcloud artifacts repositories delete $(REPOSITORY_NAME) --location=$(REGION) --project=$(PROJECT_ID) --quiet 2>/dev/null || true; \
		echo "$(GREEN)✓ Resources deleted$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

.PHONY: cost-breakdown
cost-breakdown: ## Show detailed cost breakdown
	@echo "$(GREEN)Monthly Cost Breakdown:$(NC)"
	@echo ""
	@echo "$(YELLOW)Compute:$(NC)"
	@echo "  Cloud Run API:          $$0-2    (free tier + minimal usage)"
	@echo "  Cloud Run Worker:       $$2-5    (100 videos × 5min @ $$0.000024/vCPU-sec)"
	@echo ""
	@echo "$(YELLOW)Database:$(NC)"
	@echo "  Cloud SQL (db-f1-micro): $$7.67   (shared CPU, 614MB RAM)"
	@echo "  Storage (10GB SSD):      $$1.70"
	@echo ""
	@echo "$(YELLOW)Other Services:$(NC)"
	@echo "  Cloud Tasks:            $$0      (1M operations free)"
	@echo "  Artifact Registry:      $$0.10   (storage only)"
	@echo "  Secret Manager:         $$0      (6 secrets free)"
	@echo "  Network Egress:         $$0-1    (minimal)"
	@echo ""
	@echo "  $(GREEN)Total:                  ~$$11.50-17.50/month$(NC)"

# ============================================================================
# Worker Deployment Targets
# ============================================================================

.PHONY: build-worker
build-worker: check-project ## Build worker Docker image
	@echo "$(YELLOW)Building worker Docker image...$(NC)"
	@cd ../backend && docker build \
		--platform linux/amd64 \
		-t $(WORKER_IMAGE_NAME):$(WORKER_IMAGE_TAG) \
		-f Dockerfile.worker \
		.
	@echo "$(GREEN)✓ Worker image built: $(WORKER_IMAGE_NAME):$(WORKER_IMAGE_TAG)$(NC)"

.PHONY: push-worker
push-worker: check-project ## Push worker image to Artifact Registry
	@echo "$(YELLOW)Pushing worker image to Artifact Registry...$(NC)"
	@docker tag $(WORKER_IMAGE_NAME):$(WORKER_IMAGE_TAG) $(WORKER_IMAGE_FULL)
	@docker push $(WORKER_IMAGE_FULL)
	@echo "$(GREEN)✓ Worker image pushed to $(WORKER_IMAGE_FULL)$(NC)"

.PHONY: build-push-worker
build-push-worker: build-worker push-worker ## Build and push worker image
	@echo "$(GREEN)✓ Worker image built and pushed$(NC)"

.PHONY: deploy-worker
deploy-worker: check-project build-worker push-worker ## Deploy worker with configured resources
	@echo "$(YELLOW)Deploying worker ($(WORKER_CPU) vCPU, $(WORKER_MEMORY) memory)...$(NC)"
	@gcloud run deploy notetaker-worker \
		--image=$(WORKER_IMAGE_FULL) \
		--region=$(REGION) \
		--platform=managed \
		--allow-unauthenticated \
		--cpu=$(WORKER_CPU) \
		--memory=$(WORKER_MEMORY) \
		--timeout=$(WORKER_TIMEOUT) \
		--max-instances=$(WORKER_MAX_INSTANCES) \
		--project=$(PROJECT_ID)
	@echo "$(GREEN)✓ Worker deployed with $(WORKER_CPU) vCPU$(NC)"
	@echo ""
	@echo "$(YELLOW)Worker URL:$(NC)"
	@gcloud run services describe notetaker-worker --region=$(REGION) --format='value(status.url)' --project=$(PROJECT_ID)
	@echo ""
	@echo "$(YELLOW)Next step: Grant Cloud Tasks permissions$(NC)"
	@echo "  make grant-worker-permissions"

.PHONY: deploy-worker-2cpu
deploy-worker-2cpu: ## Deploy worker with 2 vCPU (baseline configuration)
	@$(MAKE) deploy-worker WORKER_CPU=2 WORKER_MEMORY=4Gi

.PHONY: deploy-worker-4cpu
deploy-worker-4cpu: ## Deploy worker with 4 vCPU (recommended - 2x faster, 15% cheaper)
	@$(MAKE) deploy-worker WORKER_CPU=4 WORKER_MEMORY=8Gi

.PHONY: deploy-worker-8cpu
deploy-worker-8cpu: ## Deploy worker with 8 vCPU (high performance configuration)
	@$(MAKE) deploy-worker WORKER_CPU=8 WORKER_MEMORY=16Gi

.PHONY: update-worker-cpu
update-worker-cpu: check-project ## Update worker CPU/memory without rebuild (CPU=X MEMORY=XGi)
	@echo "$(YELLOW)Updating worker to $(WORKER_CPU) vCPU, $(WORKER_MEMORY) memory...$(NC)"
	@gcloud run services update notetaker-worker \
		--cpu=$(WORKER_CPU) \
		--memory=$(WORKER_MEMORY) \
		--region=$(REGION) \
		--project=$(PROJECT_ID)
	@echo "$(GREEN)✓ Worker updated to $(WORKER_CPU) vCPU$(NC)"

.PHONY: worker-status
worker-status: check-project ## Show worker service status and resources
	@echo "$(GREEN)Worker Service Status:$(NC)"
	@echo ""
	@gcloud run services describe notetaker-worker \
		--region=$(REGION) \
		--format="table(status.url,status.conditions[0].status)" \
		--project=$(PROJECT_ID) 2>/dev/null || echo "$(YELLOW)Worker not deployed$(NC)"
	@echo ""
	@echo "$(GREEN)Worker Resources:$(NC)"
	@gcloud run services describe notetaker-worker \
		--region=$(REGION) \
		--format="yaml(spec.template.spec.containers[].resources)" \
		--project=$(PROJECT_ID) 2>/dev/null || echo "$(YELLOW)Worker not deployed$(NC)"

.PHONY: worker-logs
worker-logs: check-project ## Show recent worker logs
	@gcloud run services logs read notetaker-worker \
		--region=$(REGION) \
		--limit=50 \
		--project=$(PROJECT_ID)
