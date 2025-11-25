from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from app.models import Video, Transcription, VideoStatus, Tag, VideoTag
from app.services.audio_service import (
    extract_audio,
    get_video_duration,
    cleanup_audio_file,
    split_audio_into_chunks,
    cleanup_audio_chunks,
    AudioExtractionError,
)
from app.services.transcription_service import (
    transcribe_audio,
    transcribe_audio_chunks,
    TranscriptionError,
)
from app.services.note_generation_service import generate_notes, NoteGenerationError
from app.services.r2_service import download_video, cleanup_temp_file, R2Error
from app.database import AsyncSessionLocal


async def _store_tags_for_video(db: AsyncSession, video_id: str, tag_names: list[str]) -> None:
    """
    Store tags for a video, creating new tags if they don't exist.

    Args:
        db: Database session
        video_id: UUID of video
        tag_names: List of tag names from generated notes
    """
    for tag_name in tag_names:
        # Normalize tag name
        tag_name = tag_name.strip().lower()
        if not tag_name:
            continue

        # Get or create tag
        result = await db.execute(select(Tag).filter(Tag.name == tag_name))
        tag = result.scalar_one_or_none()

        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            await db.flush()  # Get tag.id without committing
            logger.info(f"Created new tag: {tag_name}")

        # Create video-tag association if it doesn't exist
        result = await db.execute(
            select(VideoTag).filter(
                VideoTag.video_id == video_id,
                VideoTag.tag_id == tag.id
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            video_tag = VideoTag(video_id=video_id, tag_id=tag.id)
            db.add(video_tag)
            logger.info(f"Associated tag '{tag_name}' with video {video_id}")


async def process_video(
    video_id: str, max_concurrent: int = 2, chunk_threshold_mb: int = 4
) -> None:
    """
    Process video: extract audio, transcribe, and generate notes.
    Uses multiple short-lived database sessions to avoid holding connections during long operations.

    Args:
        video_id: UUID of video to process
        max_concurrent: Maximum number of concurrent transcription requests
        chunk_threshold_mb: Size threshold in MB for audio chunking
    """
    start_time = datetime.now()
    audio_path = None
    audio_size = None
    chunks = None
    chunk_threshold_bytes = chunk_threshold_mb * 1024 * 1024
    temp_video_path = None
    video_path = None

    # Session 1: Get video metadata and prepare for processing
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Video).filter(Video.id == video_id))
        video = result.scalar_one_or_none()
        if not video:
            logger.error(f"Video not found: {video_id}")
            return

        # Store video path info for processing
        r2_key = video.r2_key
        file_path = video.file_path

    try:
        # Download video from R2 if stored there
        if r2_key:
            # Session 2: Update status to downloading
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Video).filter(Video.id == video_id))
                video = result.scalar_one_or_none()
                if video:
                    video.status = VideoStatus.downloading
                    await db.commit()

            try:
                logger.info(f"Downloading video from R2: {r2_key}")
                temp_video_path, _ = download_video(r2_key)
                video_path = temp_video_path
                logger.info(f"Video downloaded to temp location: {temp_video_path}")
            except R2Error as e:
                raise AudioExtractionError(f"Failed to download video from R2: {str(e)}")
        else:
            # Use local file path for backward compatibility
            video_path = file_path

        # Session 3: Update status to extracting_audio and get duration
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Video).filter(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                video.status = VideoStatus.extracting_audio

                # Get video duration
                try:
                    duration = get_video_duration(video_path)
                    video.duration_seconds = int(duration)
                    logger.info(f"Video duration: {duration:.2f} seconds")
                except AudioExtractionError as e:
                    logger.warning(f"Could not extract video duration: {str(e)}")
                    # Continue processing even if duration extraction fails

                await db.commit()

        # Extract audio from video (no DB connection needed)
        logger.info(f"Extracting audio from {video_path}")
        audio_path, audio_size = extract_audio(video_path)
        logger.info(f"Audio extracted to {audio_path}, size: {audio_size} bytes")

        # Session 4: Update status to transcribing
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Video).filter(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                video.status = VideoStatus.transcribing
                await db.commit()

        # Transcribe audio (no DB connection needed)
        transcription_start = datetime.now()
        transcript_segments = None

        if audio_size > chunk_threshold_bytes:
            # Large audio file - split into chunks
            logger.info(
                f"Audio file {audio_size / (1024*1024):.2f} MB exceeds threshold, splitting into chunks"
            )
            chunks = split_audio_into_chunks(
                audio_path, max_chunk_size_mb=chunk_threshold_mb
            )
            logger.info(
                f"Transcribing {len(chunks)} chunks with max {max_concurrent} concurrent requests"
            )
            transcript_text, model_used, transcript_segments = await transcribe_audio_chunks(
                chunks, max_concurrent=max_concurrent
            )
        else:
            # Small audio file - transcribe directly
            logger.info(f"Transcribing audio {audio_path}")
            transcript_text, model_used, transcript_segments = transcribe_audio(audio_path)

        transcription_time = datetime.now() - transcription_start
        logger.info(f"Transcription complete, {len(transcript_text)} characters, {len(transcript_segments) if transcript_segments else 0} segments")

        # Session 5: Update status to generating_notes
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Video).filter(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                video.status = VideoStatus.generating_notes
                await db.commit()

        # Generate notes from transcript (no DB connection needed)
        notes_dict = None
        video_title = None
        tag_names = None

        try:
            logger.info(f"Generating notes from transcript")
            notes_start = datetime.now()
            notes_object, notes_model = await generate_notes(
                transcript_text, transcript_segments=transcript_segments
            )
            notes_time = datetime.now() - notes_start

            # Convert GeneratedNote Pydantic object to dict and add metadata
            notes_dict = notes_object.model_dump()
            notes_dict["model_used"] = notes_model
            notes_dict["processing_time_ms"] = int(notes_time.total_seconds() * 1000)
            notes_dict["generated_at"] = datetime.now().isoformat()

            logger.info(
                f"Notes generated successfully with summary: {notes_object.summary[:50]}..."
            )

            # Extract title and tags for DB update
            video_title = notes_object.title if notes_object.title else None
            tag_names = notes_object.tags if notes_object.tags else None

        except NoteGenerationError as e:
            logger.warning(f"Note generation failed (non-fatal): {str(e)}")
            # Continue - transcription succeeded even if notes failed

        # Calculate total processing time
        processing_time = datetime.now() - start_time

        # Session 6: Save transcription, update video status, title, and tags
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Video).filter(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                logger.error(f"Video not found during final update: {video_id}")
                return

            # Create transcription record with notes and segments
            transcription = Transcription(
                video_id=video.id,
                transcript_text=transcript_text,
                model_used=model_used,
                processing_time=transcription_time,
                audio_size=audio_size,
                transcript_segments=transcript_segments,
                notes=notes_dict,
            )
            db.add(transcription)

            # Update video title from generated notes
            if video_title:
                video.title = video_title
                logger.info(f"Updated video title to: {video_title}")

            # Update video status
            video.status = VideoStatus.completed
            await db.commit()

            # Store tags (needs to be after commit to ensure video exists)
            if tag_names:
                await _store_tags_for_video(db, video.id, tag_names)
                await db.commit()

        logger.info(f"Video {video_id} processed successfully")

    except (AudioExtractionError, TranscriptionError) as e:
        logger.error(f"Processing failed for video {video_id}: {str(e)}")

        # Session 7: Record error
        processing_time = datetime.now() - start_time
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Video).filter(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                transcription = Transcription(
                    video_id=video.id, error_message=str(e), processing_time=processing_time
                )
                db.add(transcription)

                video.status = VideoStatus.failed
                await db.commit()

    except Exception as e:
        logger.error(f"Unexpected error processing video {video_id}: {str(e)}")

        # Session 8: Update status to failed
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Video).filter(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                video.status = VideoStatus.failed
                await db.commit()

    finally:
        # Clean up temporary audio files
        if chunks:
            cleanup_audio_chunks(chunks)
        if audio_path:
            cleanup_audio_file(audio_path)
        # Clean up temporary video file (if downloaded from R2)
        if temp_video_path:
            cleanup_temp_file(temp_video_path)
