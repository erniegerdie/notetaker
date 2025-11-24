from pydantic import BaseModel, field_serializer, field_validator
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from app.models import VideoStatus, SourceType, HlsStatus


class VideoUploadResponse(BaseModel):
    id: UUID
    filename: str
    status: VideoStatus
    status_url: str

    class Config:
        from_attributes = True


class VideoStatusResponse(BaseModel):
    id: UUID
    status: VideoStatus
    uploaded_at: datetime
    duration_seconds: Optional[int] = None
    title: Optional[str] = None

    class Config:
        from_attributes = True


class VideoUpdateRequest(BaseModel):
    title: Optional[str] = None


class YouTubeSubmitRequest(BaseModel):
    """Request schema for submitting a YouTube video for processing."""
    url: str

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL looks like a YouTube URL or video ID."""
        import re

        # Allow raw video ID (11 characters)
        if re.match(r'^[a-zA-Z0-9_-]{11}$', v):
            return v

        # Allow YouTube URLs
        if 'youtube.com' in v or 'youtu.be' in v:
            return v

        raise ValueError(
            "Invalid YouTube URL. Must be a YouTube URL (youtube.com/watch?v=ID or youtu.be/ID) "
            "or an 11-character video ID"
        )


class YouTubeSubmitResponse(BaseModel):
    """Response schema after submitting a YouTube video."""
    id: UUID
    youtube_url: str
    title: Optional[str] = None
    status: VideoStatus
    source_type: SourceType
    status_url: str

    class Config:
        from_attributes = True


class TranscriptSegment(BaseModel):
    """Timestamped segment from Whisper API."""
    start: float
    end: float
    text: str


class TranscriptionResponse(BaseModel):
    video_id: UUID
    transcript_text: Optional[str]
    model_used: Optional[str]
    processing_time: Optional[timedelta] = None
    created_at: datetime
    error_message: Optional[str] = None
    audio_size: Optional[int] = None

    # Timestamped transcript segments
    transcript_segments: Optional[list[TranscriptSegment]] = None

    # Note generation fields - full JSONB with metadata
    notes: Optional['NotesData'] = None
    notes_model_used: Optional[str] = None
    notes_processing_time: Optional[str] = None

    class Config:
        from_attributes = True

    @field_serializer('processing_time')
    def serialize_processing_time(self, value: Optional[timedelta]) -> Optional[str]:
        """Convert timedelta to readable string format (e.g., '2m 30s')."""
        if value is None:
            return None
        total_seconds = int(value.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def model_post_init(self, __context) -> None:
        """Extract notes metadata after model initialization."""
        if self.notes:
            # Handle both dict and NotesData object
            if isinstance(self.notes, dict):
                self.notes_model_used = self.notes.get('model_used')
                processing_time_ms = self.notes.get('processing_time_ms')
            else:
                self.notes_model_used = getattr(self.notes, 'model_used', None)
                processing_time_ms = getattr(self.notes, 'processing_time_ms', None)

            if processing_time_ms:
                seconds = processing_time_ms // 1000
                if seconds > 0:
                    self.notes_processing_time = f"{seconds}s"
                else:
                    self.notes_processing_time = f"{processing_time_ms}ms"


class VideoListItem(BaseModel):
    id: UUID
    filename: str
    status: VideoStatus
    uploaded_at: datetime
    note_summary: Optional[str] = None
    key_points_count: Optional[int] = None
    takeaways_count: Optional[int] = None
    tags_count: Optional[int] = None
    quotes_count: Optional[int] = None

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    videos: list[VideoListItem]


class TimestampedItem(BaseModel):
    """Content item with optional timestamp reference."""
    content: str
    timestamp_seconds: Optional[float] = None


class ChapterItem(BaseModel):
    """Semantic chapter/segment of the transcript."""
    title: str
    start_seconds: float
    end_seconds: float
    description: Optional[str] = None


class SentimentTimelineItem(BaseModel):
    """Sentiment analysis at a specific point in the transcript."""
    timestamp_seconds: int
    sentiment: str  # 'positive', 'negative', 'neutral'
    intensity: int  # -100 to +100
    description: str


class ThemeItem(BaseModel):
    """Recurring theme with frequency information."""
    theme: str
    frequency: int
    key_moments: Optional[list[str]] = None


class GeneratedNote(BaseModel):
    """Structured notes generated from transcript (content only)."""
    summary: str
    key_points: list[TimestampedItem]
    detailed_notes: str
    takeaways: list[TimestampedItem]
    tags: list[str]
    quotes: Optional[list[TimestampedItem]] = None
    questions: Optional[list[str]] = None
    participants: Optional[list[str]] = None
    sentiment_timeline: Optional[list[SentimentTimelineItem]] = None
    themes: Optional[list[ThemeItem]] = None
    actionable_insights: Optional[list[str]] = None
    chapters: Optional[list[ChapterItem]] = None


class NotesData(GeneratedNote):
    """Notes with metadata - stored in JSONB field."""
    model_used: str
    processing_time_ms: int
    generated_at: str


class VideoStreamResponse(BaseModel):
    """Response schema for video streaming endpoint."""
    status: str  # "ready" | "generating" | "failed"
    source_type: str  # "youtube" | "upload"
    hls_url: Optional[str] = None  # Presigned URL if ready (upload videos)
    youtube_video_id: Optional[str] = None  # YouTube video ID (youtube videos)
    youtube_url: Optional[str] = None  # Original YouTube URL (youtube videos)
    retry_after: Optional[int] = None  # Seconds to wait before polling (if generating)
    error_message: Optional[str] = None  # Error details if failed

    class Config:
        from_attributes = True


class VideoDeleteResponse(BaseModel):
    """Response schema for video deletion."""
    id: UUID
    deleted: bool
    message: str

    class Config:
        from_attributes = True


class PresignedUploadRequest(BaseModel):
    """Request schema for generating presigned upload URL."""
    filename: str
    file_size: int
    content_type: str = "video/mp4"

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename has allowed extension."""
        from app.config import settings
        import os

        ext = os.path.splitext(v)[1].lower().lstrip('.')
        if ext not in settings.allowed_formats_list:
            raise ValueError(
                f"Invalid file extension '{ext}'. Allowed formats: {', '.join(settings.allowed_formats_list)}"
            )
        return v

    @field_validator('file_size')
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Validate file size is within limits."""
        from app.config import settings

        if v > settings.max_file_size_bytes:
            raise ValueError(
                f"File size ({v / (1024*1024):.1f}MB) exceeds maximum allowed size "
                f"({settings.max_file_size_mb}MB)"
            )
        if v <= 0:
            raise ValueError("File size must be greater than 0")
        return v


class PresignedUploadResponse(BaseModel):
    """Response schema with presigned upload URL."""
    video_id: UUID
    upload_url: str
    r2_key: str
    expires_in: int
    status_url: str


class UploadCompleteRequest(BaseModel):
    """Request schema for notifying upload completion."""
    success: bool
