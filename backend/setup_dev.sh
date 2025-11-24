#!/bin/bash

# Development setup script for Video Transcription API

set -e

echo "🚀 Setting up Video Transcription API for development..."
echo

# Check for required tools
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting." >&2; exit 1; }

echo "✅ Docker and Docker Compose found"

# Check for .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
    echo
    read -p "Press enter to continue after updating .env..."
fi

# Verify API key is set
if grep -q "your-openai-key" .env; then
    echo "⚠️  Warning: OPENAI_API_KEY still has placeholder value"
    echo "   Please update .env with your actual API key"
    exit 1
fi

echo "✅ Environment configuration found"

# Create uploads directory
mkdir -p uploads
echo "✅ Created uploads directory"

# Start services
echo
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if API is responding
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ API failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo
echo "🎉 Setup complete!"
echo
echo "📚 Next steps:"
echo "  - API documentation: http://localhost:8000/docs"
echo "  - Health check: curl http://localhost:8000/health"
echo "  - Test script: ./test_api.sh /path/to/video.mp4"
echo
echo "📊 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"
