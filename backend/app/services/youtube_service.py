"""YouTube video download service using yt-dlp."""
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
from loguru import logger
import yt_dlp

from app.config import settings


class YouTubeDownloadError(Exception):
    """Exception raised when YouTube video download fails."""
    pass


def extract_video_id(url_or_id: str) -> str:
    """
    Extract YouTube video ID from URL or validate raw video ID.

    Supports formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - VIDEO_ID (11-character alphanumeric string)

    Args:
        url_or_id: YouTube URL or video ID

    Returns:
        Extracted video ID

    Raises:
        YouTubeDownloadError: If URL format is invalid
    """
    # Pattern for YouTube video ID (11 characters: alphanumeric, dash, underscore)
    video_id_pattern = r'^[a-zA-Z0-9_-]{11}$'

    # If it's already a video ID
    if re.match(video_id_pattern, url_or_id):
        return url_or_id

    # Extract from youtube.com/watch?v=ID
    watch_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', url_or_id)
    if watch_match:
        return watch_match.group(1)

    # Extract from youtu.be/ID
    short_match = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url_or_id)
    if short_match:
        return short_match.group(1)

    raise YouTubeDownloadError(
        f"Invalid YouTube URL or video ID format: {url_or_id}. "
        "Supported formats: youtube.com/watch?v=ID, youtu.be/ID, or 11-character video ID"
    )


def download_youtube_video(url_or_id: str) -> Tuple[str, int, dict]:
    """
    Download YouTube video using yt-dlp.

    Args:
        url_or_id: YouTube URL or video ID

    Returns:
        Tuple of (file_path, file_size_bytes, metadata_dict)
        metadata includes: title, duration, thumbnail_url, description

    Raises:
        YouTubeDownloadError: If download fails for any reason
    """
    try:
        # Extract and validate video ID
        video_id = extract_video_id(url_or_id)
        logger.info(f"Downloading YouTube video: {video_id}")

        # Create uploads directory if it doesn't exist
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"yt_{video_id}_{timestamp}.%(ext)s"
        output_path = upload_dir / output_filename

        # Configure yt-dlp options
        ydl_opts = {
            'format': f'bestvideo[ext={settings.youtube_download_format}]+bestaudio[ext=m4a]/best[ext={settings.youtube_download_format}]/best',
            'outtmpl': str(output_path),
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'merge_output_format': settings.youtube_download_format,
            # Add user agent to avoid some bot detection
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        # Add duration limit if configured
        if settings.youtube_max_duration_minutes:
            max_duration_seconds = settings.youtube_max_duration_minutes * 60
            ydl_opts['match_filter'] = (
                lambda info, incomplete:
                f"Video duration ({info.get('duration', 0)}s) exceeds maximum allowed ({max_duration_seconds}s)"
                if info.get('duration', 0) > max_duration_seconds
                else None
            )

        # Download video and extract metadata
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Extract video info first
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

                if info is None:
                    raise YouTubeDownloadError(f"Could not extract video information for {video_id}")

                # Check if video is available
                if info.get('is_live'):
                    raise YouTubeDownloadError("Live streams are not supported")

                # Download the video
                logger.info(f"Starting download: {info.get('title', 'Unknown')}")
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                if "Private video" in error_msg:
                    raise YouTubeDownloadError("This video is private and cannot be downloaded")
                elif "Video unavailable" in error_msg:
                    raise YouTubeDownloadError("This video is unavailable or has been removed")
                elif "Sign in to confirm your age" in error_msg:
                    raise YouTubeDownloadError("This video is age-restricted and cannot be downloaded without authentication")
                elif "not available in your country" in error_msg:
                    raise YouTubeDownloadError("This video is not available in your region (geo-blocked)")
                else:
                    raise YouTubeDownloadError(f"Download failed: {error_msg}")

        # Find the downloaded file (yt-dlp may change extension)
        downloaded_files = list(upload_dir.glob(f"yt_{video_id}_{timestamp}.*"))
        if not downloaded_files:
            raise YouTubeDownloadError("Download completed but file not found")

        downloaded_file = downloaded_files[0]
        file_size = downloaded_file.stat().st_size

        logger.info(f"Download complete: {downloaded_file.name} ({file_size} bytes)")

        # Extract metadata
        metadata = {
            'title': info.get('title'),
            'duration': info.get('duration'),  # in seconds
            'thumbnail_url': info.get('thumbnail'),
            'description': info.get('description'),
            'uploader': info.get('uploader'),
            'upload_date': info.get('upload_date'),
        }

        return str(downloaded_file), file_size, metadata

    except YouTubeDownloadError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error downloading YouTube video {url_or_id}: {str(e)}")
        raise YouTubeDownloadError(f"Unexpected error: {str(e)}")


def cleanup_youtube_file(file_path: str) -> None:
    """
    Delete downloaded YouTube video file.

    Args:
        file_path: Path to the video file
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up YouTube video file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up YouTube video file {file_path}: {str(e)}")
