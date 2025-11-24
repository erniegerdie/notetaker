# Video Transcription & Note Generation API

FastAPI backend application that allows users to upload video files, extracts audio using ffmpeg, transcribes audio using OpenAI's native API, and generates structured notes using LiteLLM with OpenRouter.

## Features

- 📹 Video file upload (mp4, avi, mov, mkv)
- 🎵 Audio extraction using ffmpeg
- 🤖 **AI transcription using OpenAI native API** (gpt-4o-mini-transcribe)
- 📝 **Automated note generation** using LiteLLM with OpenRouter (Gemini 2.0 Flash)
- 📊 PostgreSQL database for video, transcription, and notes storage
- 🔄 Async background processing with status polling
- 🐳 Docker Compose orchestration

## Architecture

**Flow**: Video Upload → Audio Extraction (ffmpeg) → Transcription (OpenAI) → Note Generation (LiteLLM/OpenRouter) → PostgreSQL Storage

### Updated Architecture Details

1. **Transcription**: Uses OpenAI's native `gpt-4o-mini-transcribe` model directly via the OpenAI Python SDK
2. **Note Generation**: Uses LiteLLM with OpenRouter's `openrouter/google/gemini-2.0-flash-exp` model
3. **Thinking Disabled**: Note generation explicitly excludes reasoning tokens using `reasoning: {exclude: true}`

## Prerequisites

- Docker and Docker Compose
- OpenAI API key (for transcription) - Get from https://platform.openai.com/api-keys
- OpenRouter API key (for note generation) - Get from https://openrouter.ai/

## Quick Start

### 1. Clone and Setup

```bash
cd backend
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` and add both API keys:

```
DATABASE_URL=postgresql://user:password@postgres:5432/notetaker
OPENAI_API_KEY=sk-your-actual-openai-key
OPENROUTER_API_KEY=sk-or-v1-your-actual-openrouter-key
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE_MB=500
ALLOWED_VIDEO_FORMATS=mp4,avi,mov,mkv
```

### 3. Start Services

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Upload Video
```bash
POST /api/videos/upload
Content-Type: multipart/form-data

curl -X POST "http://localhost:8000/api/videos/upload" \
  -F "file=@video.mp4"
```

**Response:**
```json
{
  "id": "uuid",
  "filename": "video.mp4",
  "status": "uploaded",
  "status_url": "/api/videos/{id}/status"
}
```

### Check Status
```bash
GET /api/videos/{video_id}/status
```

**Response:**
```json
{
  "id": "uuid",
  "status": "processing",
  "uploaded_at": "2025-11-11T10:00:00Z"
}
```

Status values: `uploaded`, `processing`, `completed`, `failed`

### Get Transcription & Notes
```bash
GET /api/videos/{video_id}/transcription
```

**Response:**
```json
{
  "video_id": "uuid",
  "transcript_text": "Full transcription...",
  "model_used": "gpt-4o-mini-transcribe",
  "processing_time": "00:00:45",
  "created_at": "2025-11-11T10:01:00Z",
  "notes": "# Executive Summary\n\n...\n\n# Key Points\n- Point 1\n- Point 2",
  "notes_model_used": "openrouter/google/gemini-2.0-flash-exp",
  "notes_processing_time": "00:00:05"
}
```

## Technology Stack

- **API Framework**: FastAPI (async Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Transcription**: OpenAI native API (gpt-4o-mini-transcribe with whisper-1 fallback)
- **Note Generation**: LiteLLM with OpenRouter (Gemini 2.0 Flash)
- **Audio Extraction**: ffmpeg
- **Package Manager**: uv
- **Orchestration**: Docker Compose

## Implementation Details

### Transcription Service
Uses OpenAI's native Python SDK for direct API access:
```python
from openai import OpenAI

client = OpenAI(api_key=settings.openai_api_key)
response = client.audio.transcriptions.create(
    model="gpt-4o-mini-transcribe",
    file=audio_file,
    response_format="text"
)
```

### Note Generation Service
Uses LiteLLM with OpenRouter and reasoning tokens disabled:
```python
from litellm import completion

response = completion(
    model="openrouter/google/gemini-2.0-flash-exp",
    messages=[{"role": "user", "content": prompt}],
    extra_body={"reasoning": {"exclude": True}}
)
```

## Development

### Local Development (without Docker)

```bash
# Install dependencies
uv sync

# Start PostgreSQL separately
docker run -d -p 5432:5432 \
  -e POSTGRES_DB=notetaker \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  postgres:15

# Run migrations
uv run alembic upgrade head

# Start API server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Create Database Migration

After modifying models:
```bash
uv run alembic revision --autogenerate -m "add notes fields"
uv run alembic upgrade head
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── videos.py              # Video endpoints
│   ├── services/
│   │   ├── audio_service.py       # ffmpeg audio extraction
│   │   ├── transcription_service.py  # OpenAI native API
│   │   ├── note_generation_service.py  # LiteLLM + OpenRouter
│   │   └── video_service.py       # Processing orchestration
│   ├── utils/
│   │   └── file_handler.py        # File upload utilities
│   ├── config.py                  # Environment configuration
│   ├── database.py                # SQLAlchemy setup
│   ├── models.py                  # Database models (with notes fields)
│   ├── schemas.py                 # Pydantic schemas
│   └── main.py                    # FastAPI entry point
├── alembic/                       # Database migrations
├── uploads/                       # Video storage
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # FastAPI container
└── pyproject.toml                 # uv configuration
```

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
# Test all endpoints
./test_api.sh /path/to/video.mp4

# Or use curl directly
curl -X POST "http://localhost:8000/api/videos/upload" \
  -F "file=@video.mp4"
```

## Troubleshooting

### Missing API Keys
Make sure both `OPENAI_API_KEY` and `OPENROUTER_API_KEY` are set in `.env`

### Note Generation Fails
Notes are optional - if note generation fails, the transcription will still succeed

### OpenAI API Errors
Check your API key and billing status at https://platform.openai.com/account/billing

### OpenRouter API Errors
Verify your OpenRouter key at https://openrouter.ai/keys

## Changes from Original Implementation

1. **Transcription**: Switched from LiteLLM to OpenAI native SDK
2. **Model**: Using `gpt-4o-mini-transcribe` instead of generic `whisper-1`
3. **Note Generation**: New feature using LiteLLM with OpenRouter
4. **Reasoning Tokens**: Explicitly disabled with `reasoning: {exclude: true}`
5. **Database**: Added `notes`, `notes_model_used`, `notes_processing_time` fields
6. **Environment**: Added `OPENROUTER_API_KEY` requirement
