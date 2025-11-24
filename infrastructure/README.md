# Infrastructure Setup

This directory contains Makefile commands for managing GCP infrastructure.

## Quick Start

### 1. Configure Secrets

```bash
# Copy the template
cp .env.prod.example .env.prod

# Edit with your actual values
nano .env.prod
```

Fill in all values in `.env.prod`:
- Database connection string (Cloud SQL)
- API keys (OpenAI, OpenRouter)
- Supabase credentials
- R2 storage credentials
- GCP configuration

### 2. Upload to Secret Manager

```bash
make setup-secrets
```

This reads `.env.prod` and uploads all 16 secrets to Google Secret Manager automatically.

## Available Commands

### Infrastructure Setup

```bash
make help                      # Show all commands
make enable-apis               # Enable required GCP APIs
make create-artifact-registry  # Create Docker registry
make create-sql                # Create Cloud SQL instance
make create-tasks-queue        # Create Cloud Tasks queue
make setup-secrets             # Upload secrets from .env.prod
make setup-secrets-interactive # Prompt for each secret manually
make list-secrets              # List all configured secrets
make status                    # Show infrastructure status
make clean                     # Delete all resources (DESTRUCTIVE)
```

### Worker Deployment

```bash
make build-worker              # Build worker Docker image
make push-worker               # Push worker image to Artifact Registry
make deploy-worker             # Deploy worker with custom CPU/memory
make deploy-worker-2cpu        # Deploy with 2 vCPU + 4GB (current default)
make deploy-worker-4cpu        # Deploy with 4 vCPU + 8GB (recommended - 2x faster, 15% cheaper)
make deploy-worker-8cpu        # Deploy with 8 vCPU + 16GB (diminishing returns)
make update-worker-cpu         # Update CPU/memory without rebuild
make worker-status             # Show current worker configuration
make worker-logs               # View recent worker logs
```

## Worker Performance Optimization

### Quick Start: Deploy 4 vCPU Worker (Recommended)

Deploy the worker with 4 vCPU for optimal performance and cost:

```bash
cd infrastructure
make build-worker
make push-worker
make deploy-worker-4cpu
```

**Expected Results:**
- **Speed**: 2x faster processing (~2 minutes per 300MB video vs 4 minutes)
- **Cost**: 15% cheaper than 2 vCPU ($0.33/month per 100 videos vs $0.40/month)
- **No Code Changes**: Pure infrastructure optimization

### Verify Deployment

Check the worker configuration:

```bash
make worker-status
```

Expected output showing 4 vCPU:
```yaml
spec:
  template:
    spec:
      containers:
      - resources:
          limits:
            cpu: '4'
            memory: 8Gi
```

View recent logs:

```bash
make worker-logs
```

### Performance Testing

1. **Upload a test video** (300MB recommended):
```bash
curl -X POST "https://your-api-url/api/videos/upload" \
  -F "file=@test_video.mp4"
```

2. **Monitor processing time** in logs:
```bash
make worker-logs | grep "Processing complete"
```

Look for compression time improvements in log messages like:
```
[Worker] Compression complete: 300.00MB → 75.00MB (2m 15s)
```

3. **Compare costs** over a month of usage at [GCP Billing](https://console.cloud.google.com/billing)

### CPU Configuration Options

| Configuration | Use Case | Speed | Cost/Month (100 videos) | Notes |
|---------------|----------|-------|------------------------|-------|
| 2 vCPU + 4GB  | Light usage | Baseline | $0.40 | Current default |
| **4 vCPU + 8GB** | **Recommended** | **2x faster** | **$0.33** | **Best value** |
| 8 vCPU + 16GB | Heavy usage | 2.5x faster | $0.55 | Diminishing returns |

### Advanced Configuration

Deploy with custom CPU/memory:

```bash
make deploy-worker WORKER_CPU=6 WORKER_MEMORY=12Gi
```

Update CPU without rebuilding:

```bash
make update-worker-cpu WORKER_CPU=4 WORKER_MEMORY=8Gi
```

### Rollback

If you need to rollback to 2 vCPU:

```bash
make deploy-worker-2cpu
```

Or update without rebuild:

```bash
make update-worker-cpu WORKER_CPU=2 WORKER_MEMORY=4Gi
```

### Cost Monitoring

Monitor actual costs in GCP Console:
1. Go to [GCP Billing](https://console.cloud.google.com/billing)
2. Filter by service: **Cloud Run**
3. Group by: **SKU** (look for vCPU and Memory usage)

Expected monthly costs for 100 videos @ 300MB each:
- 2 vCPU: ~$0.40/month
- 4 vCPU: ~$0.33/month (15% cheaper)
- 8 vCPU: ~$0.55/month (38% more expensive)

## Security

⚠️ **IMPORTANT**: Never commit `.env.prod` to Git!

- `.env.prod` is already in `.gitignore`
- All secrets are stored in Google Secret Manager
- Cloud Run services access secrets via `--set-secrets` flag
- No plaintext secrets in environment variables

## Troubleshooting

### Error: `.env.prod` not found

```bash
cp .env.prod.example .env.prod
# Edit the file with your values
```

### Error: Empty secret values

Make sure all required values in `.env.prod` are filled in. Empty values will be skipped.

### Update a single secret

```bash
echo "new-value" | gcloud secrets versions add SECRET-NAME --data-file=-
```

## Files

- `.env.prod.example` - Template with all required secrets
- `.env.prod` - Your actual secrets (gitignored, DO NOT COMMIT)
- `Makefile` - Infrastructure management commands
