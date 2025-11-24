import os
import asyncio
from loguru import logger
from openai import OpenAI
from app.config import settings


class TranscriptionError(Exception):
    """Raised when transcription fails."""

    pass


def transcribe_audio(audio_path: str, model: str = None) -> tuple[str, str, list[dict]]:
    """
    Transcribe audio file using OpenAI native API with timestamp extraction.

    Args:
        audio_path: Path to audio file
        model: Model to use for transcription (defaults to settings.transcription_model)

    Returns:
        tuple: (transcript_text, model_used, transcript_segments)
        transcript_segments format: [{"start": 0.0, "end": 5.2, "text": "Hello..."}, ...]

    Raises:
        TranscriptionError: If transcription fails
    """
    if not os.path.exists(audio_path):
        raise TranscriptionError(f"Audio file not found: {audio_path}")

    # Use configured model if not specified
    if model is None:
        model = settings.transcription_model

    logger.info(
        f"[TRANSCRIPTION] Transcribing audio file {audio_path} with model {model}"
    )
    # Initialize OpenAI client with API key
    client = OpenAI(api_key=settings.openai_api_key)

    try:
        with open(audio_path, "rb") as audio_file:
            logger.info(
                f"[TRANSCRIPTION] Creating transcription request with model {model}"
            )
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
            logger.info(f"[TRANSCRIPTION] Transcription request created")

        # Extract text and segments from verbose response
        transcript_text = response.text

        if not transcript_text:
            raise TranscriptionError("Empty transcript returned")

        # Parse segments with timestamps
        segments = []
        if hasattr(response, 'segments') and response.segments:
            segments = [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                }
                for segment in response.segments
            ]
            logger.info(f"[TRANSCRIPTION] Extracted {len(segments)} timestamped segments")

        return transcript_text, model, segments

    except Exception as e:
        logger.error(f"[TRANSCRIPTION] Error transcribing audio file {audio_path}: {e}")
        # Try fallback model if primary fails
        if (
            model == settings.transcription_model
            and settings.transcription_fallback_model
        ):
            try:
                return transcribe_audio(
                    audio_path, model=settings.transcription_fallback_model
                )
            except Exception:
                pass  # Fall through to original error

        error_msg = str(e)
        raise TranscriptionError(f"Transcription failed: {error_msg}")


async def transcribe_audio_chunks(
    chunks: list[tuple[str, int]], model: str = None, max_concurrent: int = 2
) -> tuple[str, str, list[dict]]:
    """
    Transcribe multiple audio chunks with controlled concurrency and timestamp tracking.

    Args:
        chunks: List of (chunk_path, chunk_size) tuples
        model: Model to use for transcription (defaults to settings.transcription_model)
        max_concurrent: Maximum concurrent transcription requests (default 2)

    Returns:
        tuple: (combined_transcript_text, model_used, combined_segments)

    Raises:
        TranscriptionError: If transcription fails
    """
    if not chunks:
        raise TranscriptionError("No audio chunks provided")

    # Use configured model if not specified
    if model is None:
        model = settings.transcription_model

    logger.info(
        f"[TRANSCRIPTION] Transcribing {len(chunks)} chunks with max {max_concurrent} concurrent requests"
    )

    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)

    async def transcribe_chunk_async(
        chunk_index: int, chunk_path: str
    ) -> tuple[int, str, list[dict]]:
        """Transcribe a single chunk with semaphore control."""
        async with semaphore:
            logger.info(
                f"Starting transcription of chunk {chunk_index + 1}/{len(chunks)}"
            )

            # Run sync transcribe_audio in executor
            loop = asyncio.get_event_loop()
            try:
                transcript, _, segments = await loop.run_in_executor(
                    None, transcribe_audio, chunk_path, model
                )
                logger.info(
                    f"Completed chunk {chunk_index + 1}/{len(chunks)}: {len(transcript)} chars, {len(segments)} segments"
                )
                return chunk_index, transcript, segments
            except Exception as e:
                logger.error(f"Failed to transcribe chunk {chunk_index + 1}: {str(e)}")
                raise

    try:
        logger.info(f"Creating {len(chunks)} tasks for transcription")
        # Create tasks for all chunks
        tasks = [
            transcribe_chunk_async(i, chunk_path)
            for i, (chunk_path, _) in enumerate(chunks)
        ]

        logger.info(
            f"Executing {len(tasks)} tasks with concurrency limit {max_concurrent}"
        )
        # Execute with concurrency limit
        results = await asyncio.gather(*tasks)

        # Sort by chunk index
        results.sort(key=lambda x: x[0])

        # Combine transcripts and segments with cumulative time offset
        combined_transcript = " ".join(transcript for _, transcript, _ in results)
        combined_segments = []
        time_offset = 0.0

        for _, transcript, segments in results:
            # Adjust segment timestamps by cumulative offset
            for segment in segments:
                combined_segments.append({
                    "start": segment["start"] + time_offset,
                    "end": segment["end"] + time_offset,
                    "text": segment["text"]
                })

            # Update offset based on last segment's end time
            if segments:
                time_offset = combined_segments[-1]["end"]

        logger.info(
            f"Combined transcript: {len(combined_transcript)} characters, {len(combined_segments)} segments from {len(chunks)} chunks"
        )

        return combined_transcript, model, combined_segments

    except Exception as e:
        error_msg = str(e)
        raise TranscriptionError(f"Chunked transcription failed: {error_msg}")
