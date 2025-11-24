"""Worker service for processing video compression and transcription tasks.

This is a separate FastAPI application that handles CPU-intensive video processing
triggered by Google Cloud Tasks. It runs as a separate Cloud Run service.
"""
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ValidationError
from uuid import UUID
import asyncio
from loguru import logger

from app.database import AsyncSessionLocal
from app.models import Video, Transcription, VideoStatus
from app.services.video_compression_service import compress_video, VideoCompressionError
from app.services.r2_service import upload_local_file, download_video, delete_video, R2Error
from app.services.video_service import process_video
from app.config import settings
from app.utils.file_handler import delete_file
from sqlalchemy import select


# Create worker FastAPI app
app = FastAPI(
    title="Notetaker Worker Service",
    description="Background video processing service",
    version="1.0.0"
)


# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path == "/process-video":
        body = await request.body()
        logger.info(f"[Worker] Received request body: {body.decode('utf-8')}")
        # Re-create request with consumed body
        async def receive():
            return {"type": "http.request", "body": body}
        request = Request(request.scope, receive)
    response = await call_next(request)
    return response


class VideoProcessingTask(BaseModel):
    """Task payload for video processing."""
    video_id: str
    r2_key: str
    user_id: str


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy", "service": "worker"}


@app.post("/process-video")
async def process_video_task(task: VideoProcessingTask, request: Request):
    """
    Process a video: Download from R2 → Compress → Re-upload → Transcribe.

    This endpoint is called by Google Cloud Tasks. Authentication is handled
    via OIDC tokens attached to the Cloud Task.

    Args:
        task: Video processing task data
        request: FastAPI request object

    Returns:
        Processing result with status
    """
    video_id = task.video_id
    r2_key = task.r2_key
    user_id = task.user_id

    logger.info(f"[Worker] Starting processing for video {video_id}")

    # Verify this is a valid Cloud Tasks request
    # In production, you should verify the OIDC token
    # For now, we'll just log the headers
    logger.debug(f"[Worker] Request headers: {dict(request.headers)}")

    async with AsyncSessionLocal() as db:
        local_file_path = None
        compressed_path = None

        try:
            # Get video record
            result = await db.execute(
                select(Video).filter(Video.id == UUID(video_id))
            )
            video = result.scalar_one_or_none()

            if not video:
                raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

            # Check if video already has a transcription (idempotency check for retries)
            result = await db.execute(
                select(Transcription).filter(Transcription.video_id == UUID(video_id))
            )
            existing_transcription = result.scalar_one_or_none()

            if existing_transcription:
                logger.warning(f"[Worker] Video {video_id} already has transcription, skipping (Cloud Tasks retry)")
                return {
                    "status": "already_processed",
                    "video_id": video_id,
                    "message": "Video already processed (idempotent retry)"
                }

            # Update status to processing
            video.status = VideoStatus.processing
            await db.commit()

            logger.info(f"[Worker] Downloading video from R2: {r2_key}")

            # Download video from R2
            local_file_path, _ = download_video(r2_key)
            original_size = len(open(local_file_path, 'rb').read())

            logger.info(f"[Worker] Downloaded {original_size / (1024*1024):.2f}MB")

            # Compress video if enabled
            upload_path = local_file_path
            upload_size = original_size

            # Check if file is too large to compress (skip for very large files)
            skip_compression = original_size > (settings.compression_skip_threshold_mb * 1024 * 1024)

            if skip_compression:
                logger.info(
                    f"[Worker] File too large ({original_size / (1024*1024):.2f}MB), "
                    f"skipping compression (threshold: {settings.compression_skip_threshold_mb}MB)"
                )

            if settings.enable_video_compression and not skip_compression:
                try:
                    logger.info(f"[Worker] Compressing video (CRF={settings.compression_crf})...")

                    # Run compression in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    compressed_path, compressed_size = await loop.run_in_executor(
                        None,
                        compress_video,
                        local_file_path,
                        None,  # output_path (auto-generated)
                        settings.compression_crf,
                        (settings.compression_max_width, settings.compression_max_height),
                        settings.compression_max_fps,
                        settings.compression_audio_bitrate,
                        settings.compression_preset
                    )

                    reduction_pct = ((original_size - compressed_size) / original_size) * 100
                    logger.info(
                        f"[Worker] Compression complete: {original_size / (1024*1024):.2f}MB → "
                        f"{compressed_size / (1024*1024):.2f}MB ({reduction_pct:.1f}% reduction)"
                    )

                    upload_path = compressed_path
                    upload_size = compressed_size

                except VideoCompressionError as e:
                    logger.warning(f"[Worker] Compression failed, using original: {str(e)}")
                    # Continue with original file

            # Re-upload compressed video to R2
            logger.info(f"[Worker] Uploading processed video to R2...")
            final_r2_key, file_size = upload_local_file(
                upload_path,
                user_id=user_id,
                content_type="video/mp4"
            )

            logger.info(f"[Worker] Uploaded to R2: {final_r2_key}")

            # Update video record with new R2 key
            video.r2_key = final_r2_key
            video.file_path = final_r2_key
            video.file_size = file_size
            video.status = VideoStatus.uploaded
            await db.commit()

            # Delete original uncompressed video from R2 if different
            if r2_key != final_r2_key:
                try:
                    delete_video(r2_key)
                    logger.info(f"[Worker] Deleted original video from R2: {r2_key}")
                except R2Error as e:
                    logger.warning(f"[Worker] Could not delete original: {str(e)}")

            logger.info(f"[Worker] Starting transcription for video {video_id}")

            # Trigger transcription processing
            await process_video(
                video_id,
                settings.max_concurrent_transcriptions,
                settings.chunk_threshold_mb
            )

            logger.info(f"[Worker] Processing complete for video {video_id}")

            return {
                "status": "success",
                "video_id": video_id,
                "message": "Video processed and transcription started"
            }

        except Exception as e:
            logger.error(f"[Worker] Processing failed for video {video_id}: {str(e)}")

            # Update video with failed status
            try:
                result = await db.execute(
                    select(Video).filter(Video.id == UUID(video_id))
                )
                video = result.scalar_one_or_none()

                if video:
                    video.status = VideoStatus.failed

                    # Check if transcription already exists (for retries)
                    result = await db.execute(
                        select(Transcription).filter(Transcription.video_id == UUID(video_id))
                    )
                    existing_transcription = result.scalar_one_or_none()

                    if existing_transcription:
                        # Update existing transcription with error
                        existing_transcription.error_message = f"Worker processing failed: {str(e)}"
                    else:
                        # Create new transcription record with error
                        transcription = Transcription(
                            video_id=UUID(video_id),
                            error_message=f"Worker processing failed: {str(e)}"
                        )
                        db.add(transcription)

                    await db.commit()

            except Exception as db_error:
                logger.error(f"[Worker] Could not update video status: {str(db_error)}")

            raise HTTPException(status_code=500, detail=str(e))

        finally:
            # Clean up temp files
            if local_file_path:
                delete_file(local_file_path)
            if compressed_path:
                delete_file(compressed_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
