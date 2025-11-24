"""HLS video streaming service for on-demand HLS generation."""
import os
import tempfile
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime
from uuid import UUID
from loguru import logger

from app.services.r2_service import (
    download_video,
    get_r2_client,
    R2Error,
    cleanup_temp_file
)
from app.config import settings


class HlsGenerationError(Exception):
    """Exception raised when HLS generation fails."""
    pass


def generate_hls_for_video(video_id: UUID, r2_key: str, user_id: Optional[str] = None) -> str:
    """
    Generate HLS playlist and segments for a video.

    Downloads source video from R2, generates HLS using FFmpeg (copy codec),
    uploads segments back to R2, and returns the playlist R2 key.

    Args:
        video_id: UUID of the video
        r2_key: R2 key of source video
        user_id: User ID for organizing HLS files

    Returns:
        R2 key of the HLS playlist (playlist.m3u8)

    Raises:
        HlsGenerationError: If FFmpeg fails or R2 operations fail
    """
    temp_video_path = None
    temp_hls_dir = None

    try:
        # Download source video from R2
        logger.info(f"Downloading source video from R2: {r2_key}")
        temp_video_path, file_size = download_video(r2_key)
        logger.info(f"Downloaded video to {temp_video_path} ({file_size} bytes)")

        # Create temp directory for HLS output
        temp_hls_dir = tempfile.mkdtemp(prefix=f"hls_{video_id}_")
        output_playlist = os.path.join(temp_hls_dir, "playlist.m3u8")
        segment_pattern = os.path.join(temp_hls_dir, "segment%d.ts")

        logger.info(f"Generating HLS in {temp_hls_dir}")

        # FFmpeg command: copy codec (no re-encoding), 6-second segments
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", temp_video_path,
            "-c:v", "copy",  # Copy video codec (no re-encoding)
            "-c:a", "copy",  # Copy audio codec (no re-encoding)
            "-start_number", "0",
            "-hls_time", "6",  # 6-second segments
            "-hls_list_size", "0",  # Include all segments in playlist
            "-hls_segment_filename", segment_pattern,
            "-f", "hls",
            output_playlist
        ]

        # Run FFmpeg
        start_time = datetime.now()
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10-minute timeout
        )

        if result.returncode != 0:
            error_msg = f"FFmpeg failed: {result.stderr}"
            logger.error(error_msg)
            raise HlsGenerationError(error_msg)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"HLS generation complete in {elapsed:.2f}s")

        # Upload HLS files to R2
        hls_prefix = f"videos/{user_id}/{video_id}_hls" if user_id else f"videos/{video_id}_hls"
        playlist_key = upload_hls_segments(temp_hls_dir, hls_prefix)

        logger.info(f"HLS uploaded to R2: {playlist_key}")

        return playlist_key

    except subprocess.TimeoutExpired:
        raise HlsGenerationError("HLS generation timed out (>10 minutes)")
    except R2Error as e:
        raise HlsGenerationError(f"R2 operation failed: {str(e)}")
    except Exception as e:
        raise HlsGenerationError(f"Unexpected error during HLS generation: {str(e)}")
    finally:
        # Cleanup temp files
        if temp_video_path:
            cleanup_temp_file(temp_video_path)
        if temp_hls_dir:
            cleanup_hls_temp_files(temp_hls_dir)


def upload_hls_segments(local_dir: str, r2_prefix: str) -> str:
    """
    Upload HLS playlist and segments to R2.

    Args:
        local_dir: Local directory containing playlist.m3u8 and segment*.ts files
        r2_prefix: R2 prefix (e.g., "videos/user_id/video_id_hls")

    Returns:
        R2 key of the playlist (e.g., "videos/user_id/video_id_hls/playlist.m3u8")

    Raises:
        R2Error: If upload fails
    """
    try:
        client = get_r2_client()
        playlist_path = os.path.join(local_dir, "playlist.m3u8")

        if not os.path.exists(playlist_path):
            raise R2Error(f"Playlist not found: {playlist_path}")

        # Upload playlist
        playlist_key = f"{r2_prefix}/playlist.m3u8"
        with open(playlist_path, 'rb') as f:
            client.upload_fileobj(
                f,
                settings.r2_bucket_name,
                playlist_key,
                ExtraArgs={'ContentType': 'application/vnd.apple.mpegurl'}
            )
        logger.info(f"Uploaded playlist: {playlist_key}")

        # Upload all segment files
        segment_count = 0
        for filename in os.listdir(local_dir):
            if filename.endswith('.ts'):
                segment_path = os.path.join(local_dir, filename)
                segment_key = f"{r2_prefix}/{filename}"

                with open(segment_path, 'rb') as f:
                    client.upload_fileobj(
                        f,
                        settings.r2_bucket_name,
                        segment_key,
                        ExtraArgs={'ContentType': 'video/mp2t'}
                    )
                segment_count += 1

        logger.info(f"Uploaded {segment_count} HLS segments")

        return playlist_key

    except Exception as e:
        raise R2Error(f"Failed to upload HLS segments: {str(e)}")


def delete_hls_directory(r2_prefix: str) -> None:
    """
    Delete all HLS files for a video from R2.

    Args:
        r2_prefix: R2 prefix (e.g., "videos/user_id/video_id_hls")

    Raises:
        R2Error: If deletion fails
    """
    try:
        client = get_r2_client()

        # List all objects with the prefix
        response = client.list_objects_v2(
            Bucket=settings.r2_bucket_name,
            Prefix=r2_prefix
        )

        if 'Contents' not in response:
            logger.info(f"No HLS files found for prefix: {r2_prefix}")
            return

        # Delete all objects
        objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]

        client.delete_objects(
            Bucket=settings.r2_bucket_name,
            Delete={'Objects': objects_to_delete}
        )

        logger.info(f"Deleted {len(objects_to_delete)} HLS files from {r2_prefix}")

    except Exception as e:
        raise R2Error(f"Failed to delete HLS directory: {str(e)}")


def list_hls_files(r2_prefix: str) -> list[str]:
    """
    List all HLS files for a video in R2.

    Args:
        r2_prefix: R2 prefix (e.g., "videos/user_id/video_id_hls")

    Returns:
        List of R2 keys

    Raises:
        R2Error: If listing fails
    """
    try:
        client = get_r2_client()

        response = client.list_objects_v2(
            Bucket=settings.r2_bucket_name,
            Prefix=r2_prefix
        )

        if 'Contents' not in response:
            return []

        return [obj['Key'] for obj in response['Contents']]

    except Exception as e:
        raise R2Error(f"Failed to list HLS files: {str(e)}")


def check_hls_exists(r2_playlist_key: str) -> bool:
    """
    Check if HLS playlist exists in R2.

    Args:
        r2_playlist_key: R2 key of playlist.m3u8

    Returns:
        True if playlist exists, False otherwise
    """
    try:
        client = get_r2_client()

        client.head_object(
            Bucket=settings.r2_bucket_name,
            Key=r2_playlist_key
        )

        return True

    except Exception:
        return False


def get_hls_playlist_url(r2_playlist_key: str, expires_in: int = 3600) -> str:
    """
    Generate presigned URL for HLS playlist.

    Args:
        r2_playlist_key: R2 key of playlist.m3u8
        expires_in: URL expiration time in seconds (default 1 hour)

    Returns:
        Presigned URL for playlist access

    Raises:
        R2Error: If URL generation fails
    """
    try:
        client = get_r2_client()

        # If public URL is configured, use it
        if settings.r2_public_url:
            return f"{settings.r2_public_url.rstrip('/')}/{r2_playlist_key}"

        # Otherwise generate presigned URL
        url = client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.r2_bucket_name,
                'Key': r2_playlist_key
            },
            ExpiresIn=expires_in
        )

        return url

    except Exception as e:
        raise R2Error(f"Failed to generate HLS playlist URL: {str(e)}")


def cleanup_hls_temp_files(temp_dir: str) -> None:
    """
    Clean up temporary HLS directory.

    Args:
        temp_dir: Path to temporary HLS directory
    """
    try:
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up HLS temp directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Failed to clean up HLS temp directory {temp_dir}: {str(e)}")
