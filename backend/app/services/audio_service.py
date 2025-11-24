import subprocess
import tempfile
import os
from pathlib import Path
from loguru import logger


class AudioExtractionError(Exception):
    """Raised when audio extraction fails."""
    pass


def get_video_duration(video_path: str) -> float:
    """
    Get video duration in seconds using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Duration in seconds

    Raises:
        AudioExtractionError: If duration extraction fails
    """
    try:
        probe_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30, check=True)
        duration = float(result.stdout.strip())
        return duration
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise AudioExtractionError(f"Could not get video duration: {error_msg}")
    except (ValueError, subprocess.TimeoutExpired) as e:
        raise AudioExtractionError(f"Could not parse video duration: {str(e)}")


def extract_audio(video_path: str) -> tuple[str, int]:
    """
    Extract audio from video file using ffmpeg.

    Audio is optimized for speech transcription with gpt-4o-mini-transcribe:
    - Mono channel (reduces size by ~50%)
    - 16 kHz sample rate (optimal for speech recognition)
    - 32 kbps bitrate (sufficient quality for mono speech)
    - Target: Keep audio files under 25 MB API limit

    Args:
        video_path: Path to input video file

    Returns:
        Tuple of (path to extracted audio file, audio file size in bytes)

    Raises:
        AudioExtractionError: If extraction fails
    """
    if not os.path.exists(video_path):
        raise AudioExtractionError(f"Video file not found: {video_path}")

    # Create temporary file for audio output
    temp_dir = tempfile.gettempdir()
    audio_filename = f"{Path(video_path).stem}_audio.mp3"
    output_path = os.path.join(temp_dir, audio_filename)

    try:
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "libmp3lame",
            "-ac", "1",  # Convert to mono (reduces file size by ~50%)
            "-ar", "16000",  # Downsample to 16 kHz (optimal for speech recognition)
            "-b:a", "32k",  # Lower bitrate to 32 kbps (sufficient for mono speech)
            "-y",  # Overwrite output file if exists
            output_path
        ]

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            timeout=300  # 5 minute timeout
        )

        if not os.path.exists(output_path):
            raise AudioExtractionError("Audio file was not created")

        # Get audio file size
        audio_size = os.path.getsize(output_path)

        # Log audio size for monitoring
        size_mb = audio_size / (1024 * 1024)
        size_kb = audio_size / 1024
        if size_mb >= 1:
            logger.info(f"Audio extracted: {size_mb:.2f} MB")
        else:
            logger.info(f"Audio extracted: {size_kb:.2f} KB")

        return output_path, audio_size

    except subprocess.TimeoutExpired:
        raise AudioExtractionError("Audio extraction timed out")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        raise AudioExtractionError(f"ffmpeg error: {error_msg}")
    except Exception as e:
        raise AudioExtractionError(f"Unexpected error during audio extraction: {str(e)}")


def split_audio_into_chunks(audio_path: str, max_chunk_size_mb: int = 10) -> list[tuple[str, int]]:
    """
    Split audio file into smaller chunks if needed.

    Args:
        audio_path: Path to audio file
        max_chunk_size_mb: Maximum size per chunk in MB (default 10 MB to stay well under 25 MB limit)

    Returns:
        List of tuples: [(chunk_path, chunk_size), ...]

    Raises:
        AudioExtractionError: If splitting fails
    """
    if not os.path.exists(audio_path):
        raise AudioExtractionError(f"Audio file not found: {audio_path}")

    audio_size = os.path.getsize(audio_path)
    max_chunk_bytes = max_chunk_size_mb * 1024 * 1024

    # If file is already small enough, return as single chunk
    if audio_size <= max_chunk_bytes:
        logger.info(f"Audio file {audio_size / (1024*1024):.2f} MB, no splitting needed")
        return [(audio_path, audio_size)]

    # Get audio duration using ffprobe
    try:
        probe_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        total_duration = float(result.stdout.strip())
    except Exception as e:
        raise AudioExtractionError(f"Could not get audio duration: {str(e)}")

    # Calculate chunk parameters
    num_chunks = int((audio_size / max_chunk_bytes) + 1)
    chunk_duration = total_duration / num_chunks

    logger.info(f"Splitting {audio_size / (1024*1024):.2f} MB audio into {num_chunks} chunks")

    # Split audio into chunks
    chunks = []
    temp_dir = tempfile.gettempdir()
    base_name = Path(audio_path).stem

    try:
        for i in range(num_chunks):
            start_time = i * chunk_duration
            chunk_filename = f"{base_name}_chunk_{i+1:03d}.mp3"
            chunk_path = os.path.join(temp_dir, chunk_filename)

            cmd = [
                "ffmpeg",
                "-i", audio_path,
                "-ss", str(start_time),
                "-t", str(chunk_duration),
                "-acodec", "copy",  # Copy codec, no re-encoding
                "-y",
                chunk_path
            ]

            subprocess.run(cmd, check=True, capture_output=True, timeout=60)

            if not os.path.exists(chunk_path):
                raise AudioExtractionError(f"Chunk {i+1} was not created")

            chunk_size = os.path.getsize(chunk_path)
            chunks.append((chunk_path, chunk_size))

            logger.info(f"Created chunk {i+1}/{num_chunks}: {chunk_size / (1024*1024):.2f} MB")

        return chunks

    except subprocess.TimeoutExpired:
        # Cleanup partial chunks
        for chunk_path, _ in chunks:
            cleanup_audio_file(chunk_path)
        raise AudioExtractionError("Audio splitting timed out")
    except subprocess.CalledProcessError as e:
        # Cleanup partial chunks
        for chunk_path, _ in chunks:
            cleanup_audio_file(chunk_path)
        error_msg = e.stderr.decode() if e.stderr else str(e)
        raise AudioExtractionError(f"ffmpeg chunk error: {error_msg}")
    except Exception as e:
        # Cleanup partial chunks
        for chunk_path, _ in chunks:
            cleanup_audio_file(chunk_path)
        raise AudioExtractionError(f"Unexpected error during splitting: {str(e)}")


def cleanup_audio_file(audio_path: str) -> None:
    """Delete temporary audio file."""
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception as e:
        print(f"Warning: Could not delete audio file {audio_path}: {e}")


def cleanup_audio_chunks(chunks: list[tuple[str, int]]) -> None:
    """Delete all audio chunk files."""
    for chunk_path, _ in chunks:
        cleanup_audio_file(chunk_path)
