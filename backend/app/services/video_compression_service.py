"""Video compression service using FFmpeg for size reduction while maintaining quality."""
import os
import subprocess
import asyncio
import tempfile
from pathlib import Path
from typing import Tuple
from loguru import logger


class VideoCompressionError(Exception):
    """Exception raised when video compression fails."""
    pass


def compress_video(
    input_path: str,
    output_path: str = None,
    crf: int = 28,
    max_resolution: Tuple[int, int] = (1280, 720),
    max_fps: int = 30,
    audio_bitrate: str = "128k",
    preset: str = "veryfast"
) -> Tuple[str, int]:
    """
    Compress video using FFmpeg with H.264 codec.

    Reduces file size by 70-80% while maintaining high quality suitable for viewing.
    Uses CRF (Constant Rate Factor) for quality-based encoding.

    Args:
        input_path: Path to input video file
        output_path: Path for output file (creates temp file if not provided)
        crf: Constant Rate Factor (18-28 recommended, lower=better quality)
             23 = high quality (~50-70% reduction)
             26 = very good quality (~70-80% reduction)
             28 = good quality (~80-85% reduction)
        max_resolution: Maximum (width, height) - scales down if larger
        max_fps: Maximum frame rate (reduces if higher)
        audio_bitrate: Audio bitrate (128k is good quality)
        preset: FFmpeg encoding preset (faster=quicker encoding, larger files)
                ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow

    Returns:
        Tuple of (output_file_path, compressed_file_size_bytes)

    Raises:
        VideoCompressionError: If compression fails
    """
    try:
        if not os.path.exists(input_path):
            raise VideoCompressionError(f"Input file not found: {input_path}")

        # Create output path if not provided
        if not output_path:
            input_ext = Path(input_path).suffix
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f"_compressed{input_ext}",
                prefix="compressed_"
            )
            output_path = temp_file.name
            temp_file.close()

        logger.info(f"Compressing video: {input_path} → {output_path}")
        logger.info(f"Settings: CRF={crf}, preset={preset}, max_res={max_resolution}, max_fps={max_fps}")

        # Build FFmpeg command
        max_width, max_height = max_resolution

        ffmpeg_cmd = [
            "ffmpeg",
            "-i", input_path,
            # Video codec: H.264 with CRF
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", preset,  # Encoding speed preset
            # Scale down if larger than max resolution (maintains aspect ratio)
            "-vf", f"scale='min({max_width},iw)':'min({max_height},ih)':force_original_aspect_ratio=decrease",
            # Limit frame rate
            "-r", str(max_fps),
            # Audio codec: AAC
            "-c:a", "aac",
            "-b:a", audio_bitrate,
            # Optimize for streaming
            "-movflags", "+faststart",  # Move moov atom to beginning for faster streaming
            # Overwrite output file
            "-y",
            output_path
        ]

        # Run FFmpeg
        logger.info(f"Running FFmpeg compression...")
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30-minute timeout
        )

        if result.returncode != 0:
            error_msg = f"FFmpeg compression failed: {result.stderr}"
            logger.error(error_msg)
            raise VideoCompressionError(error_msg)

        # Get output file size
        if not os.path.exists(output_path):
            raise VideoCompressionError(f"Output file not created: {output_path}")

        output_size = os.path.getsize(output_path)
        input_size = os.path.getsize(input_path)

        reduction_pct = ((input_size - output_size) / input_size) * 100
        logger.info(
            f"Compression complete: {input_size / (1024*1024):.2f}MB → "
            f"{output_size / (1024*1024):.2f}MB ({reduction_pct:.1f}% reduction)"
        )

        return output_path, output_size

    except subprocess.TimeoutExpired:
        raise VideoCompressionError("Video compression timed out (>30 minutes)")
    except Exception as e:
        raise VideoCompressionError(f"Unexpected error during compression: {str(e)}")


def get_video_info(video_path: str) -> dict:
    """
    Get video information using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Dict with video info (duration, width, height, codec, bitrate, fps)

    Raises:
        VideoCompressionError: If ffprobe fails
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            raise VideoCompressionError(f"ffprobe failed: {result.stderr}")

        import json
        data = json.loads(result.stdout)

        # Extract video stream info
        video_stream = next(
            (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
            None
        )

        if not video_stream:
            raise VideoCompressionError("No video stream found")

        info = {
            'duration': float(data.get('format', {}).get('duration', 0)),
            'width': video_stream.get('width'),
            'height': video_stream.get('height'),
            'codec': video_stream.get('codec_name'),
            'bitrate': int(data.get('format', {}).get('bit_rate', 0)),
            'fps': eval(video_stream.get('r_frame_rate', '0/1'))  # e.g., "30/1" → 30.0
        }

        return info

    except subprocess.TimeoutExpired:
        raise VideoCompressionError("ffprobe timed out")
    except Exception as e:
        raise VideoCompressionError(f"Failed to get video info: {str(e)}")


def estimate_compressed_size(input_size_bytes: int, crf: int = 26) -> int:
    """
    Estimate compressed file size based on CRF setting.

    Args:
        input_size_bytes: Original file size in bytes
        crf: CRF value (18-32)

    Returns:
        Estimated compressed size in bytes
    """
    # Rough estimates based on typical compression ratios
    reduction_map = {
        18: 0.7,   # 30% reduction
        23: 0.5,   # 50% reduction
        26: 0.25,  # 75% reduction
        28: 0.2,   # 80% reduction
        32: 0.15,  # 85% reduction
    }

    # Find closest CRF value
    closest_crf = min(reduction_map.keys(), key=lambda x: abs(x - crf))
    reduction_factor = reduction_map[closest_crf]

    return int(input_size_bytes * reduction_factor)
