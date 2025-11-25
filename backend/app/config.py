from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str
    openai_api_key: str
    openrouter_api_key: str

    # Supabase authentication
    supabase_url: str = ""
    supabase_anon_key: str = ""
    # Note: JWT verification uses JWKS endpoint, not legacy JWT secret

    # Model configuration
    transcription_model: str = "whisper-1"
    transcription_fallback_model: str = "gpt-4o-mini-transcribe"
    notes_model: str = "openrouter/google/gemini-2.5-flash"
    max_concurrent_transcriptions: int = 4
    chunk_threshold_mb: int = 4

    # File handling
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 500
    allowed_video_formats: str = "mp4,avi,mov,mkv"

    # YouTube settings
    youtube_api_key: str = ""  # YouTube Data API v3 key (optional, for better metadata)
    youtube_download_format: str = "mp4"
    youtube_max_duration_minutes: int = 0  # 0 = no limit

    # Video compression settings
    enable_video_compression: bool = True
    compression_crf: int = 28  # 18-32, lower=better quality (28=fast, acceptable quality)
    compression_preset: str = "superfast"  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
    compression_max_width: int = 1280  # Reduced for faster encoding
    compression_max_height: int = 720
    compression_max_fps: int = 30
    compression_audio_bitrate: str = "96k"  # Sufficient for speech content
    compression_skip_threshold_mb: int = 1000  # Skip compression if file larger than this

    # R2 (Cloudflare) storage settings
    r2_endpoint_url: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = ""
    r2_public_url: str = ""  # Optional: public URL base for accessing videos
    presigned_url_expiration_seconds: int = 3600  # 1 hour default for upload URLs

    # GCP configuration (only used when deployed to GCP)
    gcp_project_id: str = ""
    gcp_region: str = "us-central1"
    cloud_tasks_queue: str = "video-processing-queue"
    worker_service_url: str = ""  # Cloud Run worker service URL
    cloud_tasks_service_account: str = ""  # Service account for Cloud Tasks OIDC auth

    # CORS configuration
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002"

    @property
    def allowed_formats_list(self) -> List[str]:
        return [fmt.strip() for fmt in self.allowed_video_formats.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
