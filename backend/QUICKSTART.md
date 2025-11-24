# Quick Start Guide

Get the Video Transcription API running in 5 minutes!

## Step 1: Prerequisites

Ensure you have:
- Docker and Docker Compose installed
- An OpenAI API key (get one at https://platform.openai.com/api-keys)

## Step 2: Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit `.env` and replace `your-openai-key` with your actual API key:
```
OPENAI_API_KEY=sk-...your-actual-key...
```

## Step 3: Start the Application

```bash
docker-compose up --build
```

Wait for the services to start. You should see:
```
api_1       | INFO:     Uvicorn running on http://0.0.0.0:8000
postgres_1  | database system is ready to accept connections
```

## Step 4: Test the API

Open another terminal and test the health endpoint:
```bash
curl http://localhost:8000/health
```

You should see:
```json
{"status": "healthy"}
```

## Step 5: Upload a Video

```bash
curl -X POST "http://localhost:8000/api/videos/upload" \
  -F "file=@/path/to/your/video.mp4"
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "video.mp4",
  "status": "uploaded",
  "status_url": "/api/videos/550e8400-e29b-41d4-a716-446655440000/status"
}
```

## Step 6: Check Processing Status

```bash
curl "http://localhost:8000/api/videos/{video_id}/status"
```

## Step 7: Get Transcription

Once status is `completed`:
```bash
curl "http://localhost:8000/api/videos/{video_id}/transcription"
```

## Interactive API Documentation

Open your browser and visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Using the Test Script

We've included a test script that automates the testing process:

```bash
./test_api.sh /path/to/video.mp4
```

This will:
1. Check API health
2. Upload your video
3. Poll for processing completion
4. Retrieve the transcription

## Troubleshooting

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

### API key error
Make sure your `.env` file has the correct API key:
```bash
cat .env | grep OPENAI_API_KEY
```

### Container won't start
```bash
# Check logs
docker-compose logs api

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API at http://localhost:8000/docs
- Check [plans/plan.md](../plans/plan.md) for architecture details

## Stopping the Application

```bash
# Stop services (keeps data)
docker-compose down

# Stop and remove all data
docker-compose down -v
```
