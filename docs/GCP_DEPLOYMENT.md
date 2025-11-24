# GCP Cloud Run Deployment Guide

Complete guide for deploying the Notetaker video transcription platform to Google Cloud Platform using Cloud Run, Cloud Tasks, and Cloud SQL.

## Architecture Overview

```
┌──────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│   Vercel     │────▶│  Cloud Run (API)    │────▶│  Cloud Tasks     │
│  (Next.js)   │     │  notetaker-api      │     │  video-queue     │
└──────────────┘     └─────────────────────┘     └──────┬───────────┘
                              │                          │
                              │                          │
                              │                 ┌────────▼────────────┐
                              │                 │ Cloud Run (Worker)  │
                              │                 │ notetaker-worker    │
                              │                 └─────────────────────┘
                              │
                      ┌───────▼─────────┐
                      │   Cloud SQL     │
                      │  (PostgreSQL)   │
                      └─────────────────┘
                              │
                      ┌───────▼─────────┐
                      │ Cloudflare R2   │
                      │  (Video Storage │
                      └─────────────────┘
```

## Cost Estimation

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| Cloud Run API | Serverless, scales to zero | ~$0-2 |
| Cloud Run Worker | 100 videos × 5min processing | ~$2-5 |
| Cloud SQL | db-f1-micro (614MB RAM) | ~$8 |
| Cloud Tasks | 100 tasks/month | $0 (free tier) |
| Artifact Registry | Docker images | ~$0.10 |
| Secret Manager | 7 secrets | $0 (free tier) |
| **Total** | | **~$10-15/month** |

**Compare to**: Render + Celery (~$28/month) = **~60% savings**

---

## Prerequisites

### Required Tools

```bash
# Install Google Cloud SDK
brew install google-cloud-sdk  # macOS
# OR
curl https://sdk.cloud.google.com | bash  # Linux

# Install Docker
brew install docker  # macOS

# Verify installations
gcloud --version
docker --version
make --version
```

### GCP Project Setup

```bash
# Login to GCP
gcloud auth login

# Create new project (or use existing)
gcloud projects create notetaker-prod --name="Notetaker Production"

# Set active project
gcloud config set project notetaker-prod

# Enable billing (required for Cloud Run/SQL)
# Visit: https://console.cloud.google.com/billing
```

---

## Quick Start (5 steps)

### 1. Configure GCP Project

```bash
# Set your project ID
gcloud config set project YOUR-PROJECT-ID

# Verify
make check-tools
make check-env
```

### 2. Set Up Infrastructure

```bash
# One command to create all GCP resources
make setup-gcp
```

This will:
- Enable required APIs (Cloud Run, Cloud SQL, Cloud Tasks, etc.)
- Create Artifact Registry for Docker images
- Create Cloud SQL PostgreSQL instance (~10 minutes)
- Create Cloud Tasks queue
- Set up Secret Manager secrets

### 3. Configure Secrets

All sensitive configuration is stored in **Google Secret Manager** (not environment variables).

#### Option A: Automated Setup (Recommended)

```bash
# 1. Copy the template
cd infrastructure
cp .env.prod.example .env.prod

# 2. Edit .env.prod with your actual values
nano .env.prod  # or vim, code, etc.

# 3. Upload all secrets to Secret Manager automatically
make setup-secrets
```

This reads from `.env.prod` and uploads all 16 secrets to Secret Manager in one command.

#### Option B: Interactive Setup

```bash
# Prompts for each secret individually
make setup-secrets-interactive
```

**Secret Manager stores these 16 secrets**:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `database-url` | Cloud SQL connection | `postgresql+asyncpg://postgres:PASSWORD@/notetaker?host=/cloudsql/PROJECT:REGION:INSTANCE` |
| `openai-api-key` | OpenAI API | `sk-...` |
| `openrouter-api-key` | OpenRouter API | `sk-or-v1-...` |
| `supabase-url` | Supabase URL | `https://xxxxx.supabase.co` |
| `supabase-anon-key` | Supabase anon key | `eyJhbGciOiJIUzI1NiIs...` |
| `supabase-jwt-secret` | Supabase JWT | `your-jwt-secret` |
| `r2-endpoint-url` | R2 endpoint | `https://xxxxx.r2.cloudflarestorage.com` |
| `r2-access-key-id` | R2 access key | `xxxxx` |
| `r2-secret-access-key` | R2 secret key | `xxxxx` |
| `r2-bucket-name` | R2 bucket | `notetaker-videos` |
| `r2-public-url` | R2 public URL | `https://xxxxx.r2.dev` |
| `gcp-project-id` | GCP project | `notetaker-prod` |
| `gcp-region` | GCP region | `europe-west1` |
| `cloud-tasks-queue` | Queue name | `video-processing-queue` |
| `worker-service-url` | Worker URL | *(set after deploy)* |
| `cloud-tasks-service-account` | Service account | `PROJECT@appspot.gserviceaccount.com` |

**Database URL format**:
```
postgresql+asyncpg://postgres:PASSWORD@/notetaker?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```

### 4. Deploy Services

```bash
# Build, push, and deploy everything
make deploy-all
```

This will:
- Build Docker images for API and Worker
- Push to Artifact Registry
- Deploy to Cloud Run
- **Automatically configure all secrets from Secret Manager**
- Set up Cloud SQL connections

### 5. Run Database Migrations

```bash
# Install Cloud SQL Proxy
brew install cloud-sql-proxy  # macOS
# OR
curl -o cloud-sql-proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64

# Run migrations
make db-migrate
```

### 6. Configure Worker Service URL

After deployment, get the worker URL:

```bash
gcloud run services describe notetaker-worker --region europe-west1 --format='value(status.url)'
```

Add it to Secret Manager:

```bash
# Create secret with worker URL
echo "https://notetaker-worker-xxxxx-uc.a.run.app" | \
  gcloud secrets versions add worker-service-url --data-file=-
```

Then redeploy API:

```bash
make deploy-api
```

---

## Makefile Commands Reference

### Setup & Infrastructure

```bash
make help                   # Show all available commands
make check-tools            # Verify required tools are installed
make check-env              # Check environment variables
make setup-gcp              # Initial GCP setup (one-time)
make status                 # Show deployment status
make cost-estimate          # Show estimated monthly costs
```

### Deployment

```bash
make build-all              # Build Docker images
make push-all               # Push images to Artifact Registry
make deploy-all             # Build, push, and deploy everything
make deploy-api             # Deploy API service only
make deploy-worker          # Deploy worker service only
```

### Database

```bash
make db-migrate             # Run database migrations
```

### Monitoring

```bash
make logs-api               # Tail API service logs
make logs-worker            # Tail worker service logs
```

### Rollback

```bash
make rollback-api           # Rollback API to previous revision
make rollback-worker        # Rollback worker to previous revision
```

### Cleanup

```bash
make clean                  # Delete all GCP resources (DESTRUCTIVE)
```

---

## Manual Setup (Step-by-Step)

If you prefer manual control over the Makefile:

### 1. Enable APIs

```bash
cd infrastructure
make enable-apis
```

### 2. Create Artifact Registry

```bash
make create-artifact-registry

# Configure Docker auth
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

### 3. Create Cloud SQL

```bash
make create-sql

# Set PostgreSQL password
make set-sql-password
```

### 4. Create Cloud Tasks Queue

```bash
make create-tasks-queue
```

### 5. Configure Secrets (Initial Setup)

```bash
# First time: Leave WORKER_SERVICE_URL empty in .env.prod
# You'll update it after deploying the worker (step 7)
make setup-secrets
```

**Note:** Set `WORKER_SERVICE_URL=""` (empty) in `.env.prod` for now. You'll get the actual URL after deploying the worker service.

### 6. Build & Push Images

```bash
cd ../backend
make build-api IMAGE=europe-west1-docker.pkg.dev/PROJECT/notetaker/notetaker-api:latest
make build-worker IMAGE=europe-west1-docker.pkg.dev/PROJECT/notetaker/notetaker-worker:latest
make push-api IMAGE=europe-west1-docker.pkg.dev/PROJECT/notetaker/notetaker-api:latest
make push-worker IMAGE=europe-west1-docker.pkg.dev/PROJECT/notetaker/notetaker-worker:latest
```

### 7. Deploy Services

```bash
# From root directory
make deploy-worker   # Deploy worker first
make deploy-api      # Deploy API second
```

### 8. Update Worker URL Secret

After deploying the worker, get its URL and update the secret:

```bash
cd infrastructure
make get-worker-url              # Gets URL and updates .env.prod
make setup-secrets               # Re-upload secrets with worker URL
cd ..
make deploy-api                  # Redeploy API to pick up worker URL
```

---

## Secret Manager Configuration

**All configuration is stored in Google Secret Manager** - no environment variables are exposed in Cloud Run.

### How Secrets Work

1. **Setup**: `make setup-secrets` creates 16 secrets in Secret Manager
2. **Deploy**: Cloud Run services automatically mount secrets as environment variables
3. **Runtime**: Application reads from environment variables (populated from secrets)
4. **Security**: Secrets never exposed in logs or Cloud Run configuration

### API Service Secrets

The API service has access to all 16 secrets:

- `database-url` - Cloud SQL connection string
- `openai-api-key` - OpenAI API key
- `openrouter-api-key` - OpenRouter API key
- `supabase-url` - Supabase project URL
- `supabase-anon-key` - Supabase anon key
- `supabase-jwt-secret` - Supabase JWT secret
- `r2-endpoint-url` - Cloudflare R2 endpoint
- `r2-access-key-id` - R2 access key ID
- `r2-secret-access-key` - R2 secret access key
- `r2-bucket-name` - R2 bucket name
- `r2-public-url` - R2 public URL
- `gcp-project-id` - GCP project ID
- `gcp-region` - GCP region
- `cloud-tasks-queue` - Cloud Tasks queue name
- `worker-service-url` - Worker service URL
- `cloud-tasks-service-account` - Service account email

### Worker Service Secrets

The worker service has access to 10 secrets (subset of API):

- `database-url`
- `openai-api-key`
- `openrouter-api-key`
- `r2-endpoint-url`
- `r2-access-key-id`
- `r2-secret-access-key`
- `r2-bucket-name`
- `r2-public-url`
- `gcp-project-id`
- `gcp-region`

### Updating Secrets

```bash
# Update a single secret
echo "new-value" | gcloud secrets versions add SECRET-NAME --data-file=-

# Example: Update OpenAI API key
echo "sk-new-key" | gcloud secrets versions add openai-api-key --data-file=-

# Redeploy to pick up new secret version
make deploy-api
```

### Viewing Secrets

```bash
# List all secrets
gcloud secrets list

# View secret versions (not values)
gcloud secrets versions list SECRET-NAME

# Access secret value (requires permissions)
gcloud secrets versions access latest --secret=SECRET-NAME
```

---

## Local Development with Cloud SQL

### 1. Install Cloud SQL Proxy

```bash
brew install cloud-sql-proxy
```

### 2. Start Proxy

```bash
cloud-sql-proxy PROJECT:REGION:INSTANCE &
```

### 3. Update Local .env

```bash
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@localhost:5432/notetaker
GCP_PROJECT_ID=  # Leave empty for local dev
WORKER_SERVICE_URL=  # Leave empty for local dev
```

### 4. Run Services Locally

```bash
# Terminal 1: API
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: Worker (optional, uses BackgroundTasks fallback)
uv run uvicorn app.worker:app --reload --port 8001
```

---

## Troubleshooting

### Build Errors

**Error: `uv.lock not found`**
```bash
cd backend
uv lock
```

**Error: `Permission denied` for Docker**
```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

### Deployment Errors

**Error: `Cloud SQL instance not found`**
```bash
# Wait for Cloud SQL creation to complete (~10 minutes)
make status
```

**Error: `Secret not found`**
```bash
# Verify secrets exist
gcloud secrets list

# Recreate if needed
make setup-secrets
```

### Database Errors

**Error: `Connection refused`**
```bash
# Check Cloud SQL is running
gcloud sql instances describe notetaker-db

# Verify DATABASE_URL format (Unix socket for Cloud Run)
postgresql+asyncpg://USER:PASSWORD@/DATABASE?host=/cloudsql/PROJECT:REGION:INSTANCE
```

**Error: `Too many connections`**
- Cloud SQL f1-micro has max 100 connections
- Adjust `pool_size` in [database.py](../backend/app/database.py)

### Worker Errors

**Error: `Cloud Task creation failed`**
```bash
# Verify Cloud Tasks queue exists
gcloud tasks queues describe video-processing-queue --location=europe-west1

# Check worker service is deployed
gcloud run services describe notetaker-worker --region=europe-west1
```

**Error: `Worker service unauthorized`**
```bash
# Grant Cloud Tasks permission to invoke worker
make grant-worker-permissions
```

---

## Monitoring & Logs

### View Logs

```bash
# API logs
make logs-api

# Worker logs
make logs-worker

# Or use Cloud Console
open https://console.cloud.google.com/logs
```

### Metrics

```bash
# Cloud Run metrics
open https://console.cloud.google.com/run

# Cloud SQL metrics
open https://console.cloud.google.com/sql/instances
```

---

## Updating Frontend (Vercel)

Update frontend API URL to point to Cloud Run:

```bash
# Get API URL
gcloud run services describe notetaker-api --region=europe-west1 --format='value(status.url)'

# Update Vercel environment variable
NEXT_PUBLIC_API_URL=https://notetaker-api-xxxxx-ew.a.run.app
```

Redeploy Vercel frontend to pick up new API URL.

---

## Scaling Configuration

### Auto-scaling

Cloud Run auto-scales based on requests. Configure limits:

```bash
# Update API service
gcloud run services update notetaker-api \
  --region=europe-west1 \
  --min-instances=0 \
  --max-instances=10

# Update Worker service
gcloud run services update notetaker-worker \
  --region=europe-west1 \
  --min-instances=0 \
  --max-instances=5
```

### Cloud SQL Scaling

Upgrade instance size as needed:

```bash
# Upgrade to db-g1-small (1.7GB RAM, ~$26/mo)
gcloud sql instances patch notetaker-db \
  --tier=db-g1-small
```

---

## Security Best Practices

### 1. Service Account Permissions

```bash
# Create dedicated service account
gcloud iam service-accounts create notetaker-api

# Grant minimal permissions
gcloud projects add-iam-policy-binding PROJECT \
  --member="serviceAccount:notetaker-api@PROJECT.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### 2. Secret Manager Best Practices

**✅ Do:**
- Store ALL sensitive data in Secret Manager (API keys, passwords, tokens)
- Use `--set-secrets` for Cloud Run deployment (not `--set-env-vars`)
- Rotate secrets regularly (quarterly or after exposure)
- Use IAM to restrict secret access to specific services
- Enable audit logging for secret access
- Version secrets (Secret Manager keeps history)

**❌ Don't:**
- Never commit secrets to Git (use `.env` files for local dev only)
- Never use `--set-env-vars` for sensitive data
- Never share secrets via email or Slack
- Don't grant broad secret access permissions

**Secret Rotation Example:**
```bash
# Rotate OpenAI API key
echo "sk-new-key" | gcloud secrets versions add openai-api-key --data-file=-

# Cloud Run automatically picks up latest version on next deploy
make deploy-api
```

**View Secret Access Logs:**
```bash
# See who accessed which secrets
gcloud logging read "resource.type=secretmanager.googleapis.com/Secret" --limit=50
```

### 3. Network Security

```bash
# Restrict Cloud SQL to private IP (optional)
gcloud sql instances patch notetaker-db \
  --no-assign-ip \
  --network=default
```

---

## Cost Optimization

### 1. Reduce Cloud SQL Costs

- Use db-f1-micro for development ($7.67/mo)
- Upgrade to db-g1-small for production ($26/mo)
- Enable automatic backups (included)

### 2. Optimize Cloud Run

- Set `--min-instances=0` to scale to zero
- Use `--cpu-throttling` to reduce idle costs
- Configure appropriate `--memory` and `--cpu`

### 3. Monitor Usage

```bash
# Check current month's costs
gcloud billing accounts list
open https://console.cloud.google.com/billing
```

---

## Production Checklist

- [ ] Enable Cloud SQL automatic backups
- [ ] Set up Cloud Monitoring alerts
- [ ] Configure custom domain for Cloud Run
- [ ] Enable Cloud Armor (DDoS protection)
- [ ] Set up CI/CD with Cloud Build
- [ ] Configure log retention policies
- [ ] Set up error reporting (Sentry/Cloud Error Reporting)
- [ ] Enable Cloud SQL high availability (for production)
- [ ] Configure backup retention
- [ ] Set up health check monitoring

---

## Next Steps

1. **Deploy to Staging**: Test deployment with staging project
2. **CI/CD**: Set up Cloud Build for automated deployments
3. **Monitoring**: Configure alerts for errors and performance
4. **Scaling**: Monitor usage and adjust instance sizes
5. **Backup**: Test database backup and restore procedures

---

## Support

- **Makefile Help**: `make help`
- **GCP Documentation**: https://cloud.google.com/run/docs
- **Cloud SQL Guide**: https://cloud.google.com/sql/docs
- **Cloud Tasks**: https://cloud.google.com/tasks/docs

---

**Deployment complete!** 🎉

Your video transcription platform is now running on GCP Cloud Run with:
- ✅ Serverless API (scales to zero)
- ✅ Background job processing
- ✅ Managed PostgreSQL database
- ✅ ~60% cost savings vs Render

Estimated cost: **$10-15/month** for 100 videos/month.
