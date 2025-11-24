# Development Setup Guide

Quick guide for running the backend locally with hot reload.

## Prerequisites

- Python 3.11+
- uv installed
- Docker (for PostgreSQL)
- OpenAI API key
- OpenRouter API key

## Setup Steps

### 1. Start PostgreSQL

```bash
docker-compose up -d
```

This starts only PostgreSQL on port 5432.

### 2. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/notetaker
OPENAI_API_KEY=sk-your-actual-openai-key
OPENROUTER_API_KEY=sk-or-v1-your-actual-openrouter-key
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=500
ALLOWED_VIDEO_FORMATS=mp4,avi,mov,mkv
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Run Database Migrations

```bash
uv run alembic upgrade head
```

If you need to create a new migration after model changes:

```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

### 5. Start API Server with Hot Reload

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` and will automatically reload when you make code changes.

## Development Workflow

### Making Code Changes

1. Edit Python files in `app/`
2. Server automatically reloads
3. Test changes at http://localhost:8000/docs

### Database Changes

1. Modify models in `app/models.py`
2. Create migration: `uv run alembic revision --autogenerate -m "add new field"`
3. Review migration in `alembic/versions/`
4. Apply migration: `uv run alembic upgrade head`

### Testing API

```bash
# Health check
curl http://localhost:8000/health

# Upload video
curl -X POST "http://localhost:8000/api/videos/upload" \
  -F "file=@test.mp4"

# Check status
curl "http://localhost:8000/api/videos/{video_id}/status"

# Get transcription + notes
curl "http://localhost:8000/api/videos/{video_id}/transcription"
```

Or use the interactive docs at http://localhost:8000/docs

## Useful Commands

```bash
# View logs
docker-compose logs -f postgres

# Stop PostgreSQL
docker-compose down

# Stop and remove data
docker-compose down -v

# Check API is running
curl http://localhost:8000/health

# View database
docker exec -it backend-postgres-1 psql -U user -d notetaker
```

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   └── videos.py              # API endpoints
│   ├── services/
│   │   ├── audio_service.py       # ffmpeg extraction
│   │   ├── transcription_service.py  # OpenAI transcription
│   │   ├── note_generation_service.py  # LiteLLM notes
│   │   └── video_service.py       # Orchestration
│   ├── models.py                  # Database models
│   ├── schemas.py                 # Pydantic schemas
│   ├── config.py                  # Settings
│   └── main.py                    # FastAPI app
├── alembic/                       # Migrations
├── uploads/                       # Video storage
└── docker-compose.yml             # PostgreSQL only
```

## Troubleshooting

### Port 5432 already in use
```bash
# Stop existing PostgreSQL
docker-compose down
# Or change port in docker-compose.yml and DATABASE_URL
```

### Module not found
```bash
uv sync
```

### Database connection error
```bash
# Check PostgreSQL is running
docker-compose ps
# Check connection string in .env
```

### ffmpeg not found
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

## Production Deployment

For production, uncomment and configure the `api` service in `docker-compose.yml` to run the full stack with Docker.
