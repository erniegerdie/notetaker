#!/bin/bash
# Helper script to get the Worker Service URL after deployment

set -e

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Getting Worker Service URL...${NC}"

# Get region and project
REGION=$(gcloud config get-value compute/region 2>/dev/null || echo "europe-west1")
PROJECT=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT" ]; then
    echo -e "${RED}Error: No GCP project configured${NC}"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${YELLOW}Project: ${PROJECT}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo ""

# Get worker service URL
WORKER_URL=$(gcloud run services describe notetaker-worker \
    --region=$REGION \
    --format='value(status.url)' \
    2>/dev/null)

if [ -z "$WORKER_URL" ]; then
    echo -e "${RED}Error: Worker service not found${NC}"
    echo "Deploy the worker service first with: make deploy-worker"
    exit 1
fi

echo -e "${GREEN}Worker Service URL:${NC}"
echo "$WORKER_URL"
echo ""

# Update .env.prod if it exists
if [ -f ".env.prod" ]; then
    echo -e "${YELLOW}Updating .env.prod...${NC}"

    # Check if WORKER_SERVICE_URL exists in .env.prod
    if grep -q "^WORKER_SERVICE_URL=" .env.prod; then
        # Update existing value
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|^WORKER_SERVICE_URL=.*|WORKER_SERVICE_URL=$WORKER_URL|" .env.prod
        else
            # Linux
            sed -i "s|^WORKER_SERVICE_URL=.*|WORKER_SERVICE_URL=$WORKER_URL|" .env.prod
        fi
        echo -e "${GREEN}✓ Updated WORKER_SERVICE_URL in .env.prod${NC}"
    else
        # Append if doesn't exist
        echo "WORKER_SERVICE_URL=$WORKER_URL" >> .env.prod
        echo -e "${GREEN}✓ Added WORKER_SERVICE_URL to .env.prod${NC}"
    fi

    echo ""
    echo -e "${YELLOW}Next step: Update Secret Manager${NC}"
    echo "Run: echo \"$WORKER_URL\" | gcloud secrets versions add worker-service-url --data-file=-"
else
    echo -e "${YELLOW}Note: .env.prod not found. Create it to auto-update.${NC}"
fi
