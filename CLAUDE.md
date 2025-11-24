# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack video transcription platform with FastAPI backend and Next.js frontend. Supports both video uploads and YouTube downloads, with AI-powered transcription and intelligent note generation.

**Status**: Full MVP with YouTube integration, collections, tags, and AI note generation

### Core Features
- **Multi-source Input**: Direct file uploads (mp4, avi, mov, mkv) + YouTube URL downloads (via yt-dlp)
- **AI Transcription**: OpenAI Whisper with verbose_json format for timestamped segments
- **Intelligent Notes**: LLM-generated summaries, key points, takeaways, quotes, and semantic chapters
- **Organization**: Collections and tagging system for video library management
- **Time-Synced UI**: Clickable timestamps throughout notes that link to specific video moments

## Technology Stack

### Backend
- **API**: FastAPI (async Python, uvicorn)
- **Database**: PostgreSQL with SQLAlchemy ORM (async) + Alembic migrations
- **AI Transcription**: OpenAI Whisper API (native client, not LiteLLM wrapper)
- **AI Note Generation**: LiteLLM (supports multiple providers)
- **Video Processing**: ffmpeg for audio extraction, yt-dlp for YouTube downloads
- **Package Manager**: uv (Python dependency management)

### Frontend
- **Framework**: Next.js 15 (React 18, App Router)
- **Styling**: Tailwind CSS + shadcn/ui components
- **State**: TanStack Query (React Query) for server state
- **Forms**: React Hook Form + Zod validation
- **UI Components**: Radix UI primitives (dialog, dropdown, tabs, toast, etc.)

### Infrastructure
- **Orchestration**: Docker Compose (backend + PostgreSQL)
- **Development**: Hot reload for both backend (uvicorn) and frontend (Next.js)

## Project Structure

```
notetaker/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI app + CORS config
│   │   ├── config.py                    # Environment settings (Pydantic)
│   │   ├── database.py                  # AsyncSession + connection pool
│   │   ├── models.py                    # SQLAlchemy models (Video, Transcription, Collection, Tag)
│   │   ├── schemas.py                   # Pydantic request/response schemas
│   │   ├── api/
│   │   │   ├── videos.py                # Video upload/YouTube/status/transcription endpoints
│   │   │   └── collections.py           # Collection + tag management
│   │   ├── services/
│   │   │   ├── video_service.py         # Orchestrates full processing pipeline
│   │   │   ├── audio_service.py         # ffmpeg extraction + chunking for large files
│   │   │   ├── transcription_service.py # OpenAI Whisper with segment timestamps
│   │   │   ├── note_generation_service.py # LLM structured notes + chapters
│   │   │   ├── youtube_service.py       # yt-dlp integration + metadata extraction
│   │   │   └── llm.py                   # Shared LiteLLM chat wrapper
│   │   └── utils/
│   │       └── file_handler.py          # Upload validation + disk operations
│   ├── alembic/                         # Database migrations
│   ├── scripts/                         # Test utilities (audio, transcription, DB reset)
│   ├── uploads/                         # Video/audio file storage (gitignored)
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── pyproject.toml                   # uv dependencies
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                   # Root layout + providers
│   │   ├── page.tsx                     # Home page (video list)
│   │   ├── videos/[id]/page.tsx         # Video detail + transcription view
│   │   └── collections/page.tsx         # Collections management
│   ├── components/                      # Reusable UI components
│   ├── lib/                             # Utilities + API client
│   └── package.json
└── plans/                                # Implementation documentation
```

## Key Architecture Patterns

### Processing Pipeline
**Upload/YouTube → Background Task → Audio Extraction → Whisper Transcription → LLM Note Generation → PostgreSQL**

1. **Video Ingestion**: Upload file OR YouTube URL via yt-dlp
2. **Async Processing**: FastAPI BackgroundTasks handles extraction/transcription without blocking response
3. **Audio Extraction**: ffmpeg extracts audio, automatically chunks large files (>25MB by default)
4. **Transcription**: OpenAI Whisper with `verbose_json` + `timestamp_granularities=["segment"]`
5. **Note Generation**: LLM analyzes transcript to create structured notes with timestamp references
6. **Status Polling**: Frontend polls `/status` endpoint until completion

### Database Schema
- **videos**: Source metadata (file/YouTube), status tracking, collection relationship
- **transcriptions**: One-to-one with videos, stores transcript + segments (JSONB) + notes (JSONB)
- **collections**: Organizational folders for videos
- **tags**: Many-to-many with videos via `video_tags` join table

### Async Architecture
- **SQLAlchemy async**: All DB operations use `AsyncSession` with connection pooling
- **Background tasks**: Non-blocking video processing, immediate API response
- **Concurrent transcription**: Configurable semaphore limits parallel OpenAI API calls
- **Chunked processing**: Large audio files split into segments and transcribed in parallel

### JSONB Data Structures

**transcript_segments** (in transcriptions table):
```json
[
  {"start": 0.0, "end": 5.2, "text": "Hello and welcome..."},
  {"start": 5.2, "end": 10.8, "text": "Today we'll discuss..."}
]
```

**notes** (in transcriptions table):
```json
{
  "summary": {"content": "...", "model_used": "gpt-4o-mini", ...},
  "key_points": [
    {"content": "Main idea here", "timestamp_seconds": 15.3, ...}
  ],
  "takeaways": [...],
  "quotes": [...],
  "chapters": [
    {"title": "Introduction", "start_time": 0.0, "end_time": 120.5, ...}
  ]
}
```

## Development Commands

### Backend (from `/backend` directory)

```bash
# First-time setup
uv sync                              # Install all dependencies

# Database
uv run alembic upgrade head          # Apply migrations
uv run alembic revision --autogenerate -m "description"  # Create migration
uv run python scripts/reset_database.py  # Reset database (destructive!)

# Development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Docker
docker-compose up --build            # Start backend + PostgreSQL
docker-compose down -v               # Stop and remove volumes

# Testing utilities (in scripts/)
uv run python scripts/test_audio_extraction.py <video_id>
uv run python scripts/test_transcription.py <video_id>
uv run python scripts/test_audio_cleanup.py
```

### Frontend (from `/frontend` directory)

```bash
# First-time setup
npm install                          # or pnpm/yarn

# Development
npm run dev                          # Next.js dev server (port 3000)
npm run build                        # Production build
npm run start                        # Production server
npm run lint                         # ESLint check
```

### Full Stack Development

Run backend (Docker) + frontend (npm) simultaneously in separate terminals:
```bash
# Terminal 1
cd backend && docker-compose up

# Terminal 2
cd frontend && npm run dev
```

## Environment Configuration

### Backend (`backend/.env`)

Required variables:
```bash
# Database (use 'postgres' as host when running in Docker, 'localhost' when running locally)
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/notetaker

# OpenAI API (required for Whisper transcription)
OPENAI_API_KEY=sk-...

# File storage
UPLOAD_DIR=/app/uploads              # Use /app/uploads in Docker, ./uploads locally
MAX_FILE_SIZE_MB=500
ALLOWED_VIDEO_FORMATS=mp4,avi,mov,mkv

# AI Models
TRANSCRIPTION_MODEL=whisper-1        # OpenAI Whisper model
TRANSCRIPTION_FALLBACK_MODEL=whisper-1
NOTES_MODEL=gpt-4o-mini              # LLM for note generation

# Processing limits
MAX_CONCURRENT_TRANSCRIPTIONS=3      # Parallel API call limit
CHUNK_THRESHOLD_MB=25                # Auto-chunk audio files larger than this
```

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API URL
```

## API Endpoints

### Videos
- `POST /api/videos/upload` - Upload video file (multipart/form-data)
- `POST /api/videos/youtube` - Submit YouTube URL for download + processing
- `GET /api/videos` - List all videos with filters (collection, tags, status)
- `GET /api/videos/{video_id}` - Get single video metadata
- `GET /api/videos/{video_id}/status` - Poll processing status
- `GET /api/videos/{video_id}/transcription` - Get transcription + notes
- `PATCH /api/videos/{video_id}` - Update video metadata (title, collection)
- `DELETE /api/videos/{video_id}` - Delete video + associated files

### Collections & Tags
- `GET /api/collections` - List all collections
- `POST /api/collections` - Create collection
- `GET /api/collections/{collection_id}` - Get collection details
- `PATCH /api/collections/{collection_id}` - Update collection
- `DELETE /api/collections/{collection_id}` - Delete collection
- `GET /api/tags` - List all tags
- `POST /api/tags` - Create tag
- `POST /api/videos/{video_id}/tags` - Add tags to video
- `DELETE /api/videos/{video_id}/tags/{tag_id}` - Remove tag from video

Interactive docs: http://localhost:8000/docs (Swagger UI)

## Implementation Guidelines

### Backend Patterns

**Always use uv**: Prefix all Python commands with `uv run` (e.g., `uv run uvicorn`, `uv run alembic`, `uv run python`)

**Database operations**:
- Use async SQLAlchemy with `AsyncSession` from dependency injection
- All queries should await database calls
- Use transactions for multi-step operations
- Foreign key relationships: Collections (optional), Tags (many-to-many), Transcription (one-to-one required)

**Service layer architecture**:
- `video_service.py`: High-level orchestration, calls other services
- `audio_service.py`: Pure ffmpeg operations, no DB access
- `transcription_service.py`: Pure OpenAI API calls, no DB access
- `note_generation_service.py`: Pure LLM calls, no DB access
- `youtube_service.py`: Pure yt-dlp operations, no DB access
- API routes handle DB operations and coordinate service calls

**Error handling**:
- Raise custom exceptions from services (`TranscriptionError`, `AudioExtractionError`, etc.)
- Catch in API routes and return appropriate HTTP status codes
- Use loguru for structured logging with context
- Always clean up temporary files in finally blocks
- Update video status to "failed" + store error_message in transcription on failures

**Background processing**:
- Use FastAPI `BackgroundTasks` for video processing pipeline
- Semaphore limits concurrent OpenAI API calls (settings.max_concurrent_transcriptions)
- For large audio files: automatic chunking at settings.chunk_threshold_mb
- Chunked transcriptions run in parallel and are merged with timestamps

### Frontend Patterns

**API communication**:
- All API calls through centralized client in `lib/api.ts`
- Use TanStack Query (React Query) for server state management
- Polling pattern for status updates (see video detail page)

**Component structure**:
- Use shadcn/ui components (in `components/ui/`)
- Custom components in `components/` directory
- Server components by default, client components only when needed (forms, interactivity)

**Styling**:
- Tailwind utility classes
- Use `cn()` helper for conditional class merging
- Follow shadcn/ui design patterns

### Code Quality Standards

- **Type safety**: Full TypeScript in frontend, Pydantic schemas in backend
- **Validation**: Zod in frontend, Pydantic in backend
- **HTTP status codes**: 200 (success), 201 (created), 404 (not found), 500 (server error)
- **Logging**: Use loguru with descriptive context in backend
- **Cleanup**: Always remove temporary audio files after processing
- **Pythonic style**: Use type hints, async/await, context managers
