import uuid
from sqlalchemy import Column, String, BigInteger, Enum, ForeignKey, Text, Interval, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class VideoStatus(str, enum.Enum):
    # Upload phase
    uploading = "uploading"  # Video is being compressed and uploaded to storage
    uploaded = "uploaded"  # Upload complete, ready for processing

    # Processing phases (granular pipeline tracking)
    downloading = "downloading"  # Downloading from R2 (if applicable)
    extracting_audio = "extracting_audio"  # ffmpeg audio extraction in progress
    transcribing = "transcribing"  # Whisper API transcription in progress
    generating_notes = "generating_notes"  # LLM note generation in progress

    # Terminal states
    completed = "completed"  # All processing complete
    failed = "failed"  # Processing failed at any stage


class HlsStatus(str, enum.Enum):
    generating = "generating"
    ready = "ready"
    failed = "failed"


class Collection(Base):
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Auth: owner of collection
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    videos = relationship("Video", back_populates="collection")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    color = Column(String, nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Auth: owner of tag
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    videos = relationship("Video", secondary="video_tags", back_populates="tags")


class VideoTag(Base):
    __tablename__ = "video_tags"

    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SourceType(str, enum.Enum):
    upload = "upload"
    youtube = "youtube"


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    title = Column(String, nullable=True)  # Custom user-defined title
    file_path = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    duration_seconds = Column(BigInteger, nullable=True)  # Video duration in seconds
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    status = Column(Enum(VideoStatus), default=VideoStatus.uploaded, nullable=False, index=True)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Auth: owner of video

    # YouTube-specific fields
    source_type = Column(Enum(SourceType), default=SourceType.upload, nullable=False, index=True)
    youtube_url = Column(String, nullable=True)  # Original YouTube URL if source is YouTube

    # R2 storage fields
    r2_key = Column(String, nullable=True, index=True)  # R2 object key (if stored in R2)

    # HLS streaming fields
    hls_playlist_key = Column(String, nullable=True, index=True)  # R2 key for playlist.m3u8
    hls_status = Column(Enum(HlsStatus), nullable=True, index=True)  # null/generating/ready/failed
    hls_generated_at = Column(DateTime(timezone=True), nullable=True)  # When HLS was generated
    hls_error_message = Column(Text, nullable=True)  # Error details if HLS generation failed

    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete timestamp

    transcription = relationship("Transcription", back_populates="video", uselist=False)
    collection = relationship("Collection", back_populates="videos")
    tags = relationship("Tag", secondary="video_tags", back_populates="videos")


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    transcript_text = Column(Text)
    model_used = Column(String)
    processing_time = Column(Interval)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    error_message = Column(Text, nullable=True)
    audio_size = Column(BigInteger, nullable=True)

    # Timestamped transcript segments from Whisper API
    # Structure: [{"start": 0.0, "end": 5.2, "text": "Hello..."}, ...]
    transcript_segments = Column(JSONB, nullable=True)

    # Note generation fields - full JSONB structure
    # Structure: {
    #   "content": "...",
    #   "model_used": "gpt-4",
    #   "processing_time_ms": 1250,
    #   "generated_at": "2025-11-14T...",
    #   "type": "summary"
    # }
    notes = Column(JSONB, nullable=True)

    video = relationship("Video", back_populates="transcription")
