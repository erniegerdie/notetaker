from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import uuid

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import Video, Transcription, VideoStatus, SourceType, HlsStatus
from app.schemas import (
    VideoUploadResponse,
    VideoStatusResponse,
    VideoUpdateRequest,
    TranscriptionResponse,
    VideoListResponse,
    VideoListItem,
    NotesData,
    YouTubeSubmitRequest,
    YouTubeSubmitResponse,
    VideoStreamResponse,
    VideoDeleteResponse,
    PresignedUploadRequest,
    PresignedUploadResponse,
    UploadCompleteRequest,
)
from app.utils.file_handler import validate_video_file, save_upload_file, save_upload_to_r2, delete_file
from app.services.r2_service import (
    delete_video,
    generate_presigned_upload_url,
    verify_r2_object_exists,
    R2Error
)
from app.services.hls_service import (
    generate_hls_for_video,
    get_hls_playlist_url,
    delete_hls_directory,
    HlsGenerationError
)
from app.services.youtube_service import extract_video_id
from app.utils.file_handler import delete_file
from datetime import datetime
from app.config import settings
from loguru import logger

# Import Cloud Tasks service (required for video processing)
from app.services.cloud_tasks_service import create_video_processing_task, CloudTasksError

# Log warning if Cloud Tasks is not configured
if not settings.gcp_project_id or not settings.worker_service_url:
    logger.warning("Cloud Tasks configuration missing! Video processing will fail. GCP_PROJECT_ID and WORKER_SERVICE_URL are required.")

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("/upload", response_model=VideoUploadResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Upload a video file and initiate compression/upload process."""
    # Validate file
    validate_video_file(file)

    # Save to temp file
    temp_path, original_size = await save_upload_file(file)
    logger.info(f"Video saved to temp: {temp_path} ({original_size / (1024*1024):.2f}MB)")

    # Upload to R2 immediately (uncompressed)
    r2_key, file_size = upload_local_file(temp_path, user_id=user_id)
    logger.info(f"Video uploaded to R2: {r2_key}")

    # Create database record
    video = Video(
        filename=file.filename,
        file_path=r2_key,
        r2_key=r2_key,
        file_size=file_size,
        status=VideoStatus.uploading,
        source_type=SourceType.upload,
        user_id=user_id
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    logger.info(f"Video {video.id} created, queuing processing task")

    # Queue processing task via Cloud Tasks
    try:
        create_video_processing_task(str(video.id), r2_key, user_id)
        logger.info(f"Created Cloud Task for video {video.id}")
    except CloudTasksError as e:
        logger.error(f"Cloud Task creation failed: {str(e)}")
        # Update video status to failed
        video.status = VideoStatus.failed
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to queue video processing: {str(e)}")

    # Clean up temp file
    delete_file(temp_path)

    return VideoUploadResponse(
        id=video.id,
        filename=video.filename,
        status=video.status,
        status_url=f"/api/videos/{video.id}/status"
    )


@router.post("/upload/presigned", response_model=PresignedUploadResponse, status_code=201)
async def generate_presigned_upload(
    request: PresignedUploadRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """
    Generate presigned URL for direct R2 upload.

    This endpoint creates a video record and returns a presigned URL that
    the frontend can use to upload directly to R2, bypassing the API.
    After upload, the frontend must call /upload/complete to trigger processing.
    """
    try:
        # Generate unique R2 key
        from pathlib import Path
        file_ext = Path(request.filename).suffix
        unique_id = uuid.uuid4()
        r2_key = f"videos/{user_id}/{unique_id}{file_ext}"

        logger.info(f"Generating presigned upload URL for {request.filename} ({request.file_size / (1024*1024):.2f}MB)")

        # Generate presigned upload URL
        upload_url = generate_presigned_upload_url(
            r2_key,
            content_type=request.content_type,
            expires_in=settings.presigned_url_expiration_seconds
        )

        # Create video record with uploading status
        video = Video(
            filename=request.filename,
            file_path=r2_key,
            r2_key=r2_key,
            file_size=request.file_size,
            status=VideoStatus.uploading,
            source_type=SourceType.upload,
            user_id=user_id
        )
        db.add(video)
        await db.commit()
        await db.refresh(video)

        logger.info(f"Video {video.id} created with presigned URL (expires in {settings.presigned_url_expiration_seconds}s)")

        return PresignedUploadResponse(
            video_id=video.id,
            upload_url=upload_url,
            r2_key=r2_key,
            expires_in=settings.presigned_url_expiration_seconds,
            status_url=f"/api/videos/{video.id}/status"
        )

    except Exception as e:
        logger.error(f"Failed to generate presigned upload URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate upload URL: {str(e)}"
        )


@router.post("/{video_id}/upload/complete", response_model=VideoUploadResponse)
async def complete_upload(
    video_id: UUID,
    request: UploadCompleteRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """
    Complete upload after frontend uploads directly to R2.

    This endpoint verifies the upload succeeded and triggers processing.
    Called by frontend after successfully uploading to the presigned URL.
    """
    # Get video record
    result = await db.execute(
        select(Video).filter(Video.id == video_id, Video.user_id == user_id, Video.deleted_at.is_(None))
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.status != VideoStatus.uploading:
        raise HTTPException(
            status_code=400,
            detail=f"Video is not in uploading state (current: {video.status})"
        )

    try:
        if not request.success:
            # Frontend reported upload failure
            logger.warning(f"Frontend reported upload failure for video {video_id}")
            video.status = VideoStatus.failed
            await db.commit()
            raise HTTPException(status_code=400, detail="Upload failed")

        # Verify file exists in R2
        logger.info(f"Verifying R2 upload for video {video_id}: {video.r2_key}")
        verify_r2_object_exists(video.r2_key)

        # Update status to uploaded
        video.status = VideoStatus.uploaded
        await db.commit()

        logger.info(f"Video {video_id} upload verified, queueing processing task")

        # Queue processing task via Cloud Tasks
        try:
            create_video_processing_task(str(video.id), video.r2_key, user_id)
            logger.info(f"Created Cloud Task for video {video.id}")
        except CloudTasksError as e:
            logger.error(f"Cloud Task creation failed: {str(e)}")
            video.status = VideoStatus.failed
            await db.commit()
            raise HTTPException(status_code=500, detail=f"Failed to queue video processing: {str(e)}")

        return VideoUploadResponse(
            id=video.id,
            filename=video.filename,
            status=video.status,
            status_url=f"/api/videos/{video.id}/status"
        )

    except R2Error as e:
        logger.error(f"R2 verification failed for video {video_id}: {str(e)}")
        video.status = VideoStatus.failed
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"Upload verification failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Upload completion failed for video {video_id}: {str(e)}")
        video.status = VideoStatus.failed
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Upload completion failed: {str(e)}"
        )


@router.post("/youtube", response_model=YouTubeSubmitResponse, status_code=201)
async def submit_youtube_video(
    request: YouTubeSubmitRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """
    Submit a YouTube video URL for processing.

    Accepts YouTube URLs in these formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - VIDEO_ID (11-character video identifier)
    """
    try:
        logger.info(f"Processing YouTube video request: {request.url}")

        # Create database record with "uploading" status
        video = Video(
            filename="",  # Will be set after download
            title="",  # Will be set after download
            file_path="",  # Will be set after upload
            file_size=0,  # Will be set after upload
            status=VideoStatus.uploading,
            source_type=SourceType.youtube,
            youtube_url=request.url,
            user_id=user_id
        )
        db.add(video)
        await db.commit()
        await db.refresh(video)

        logger.info(f"YouTube video {video.id} created, queueing processing task")

        # Queue processing task via Cloud Tasks
        # Note: For YouTube videos, r2_key will be empty until download completes
        # Worker will need to handle YouTube download/upload before transcription
        try:
            create_video_processing_task(str(video.id), "", user_id)
            logger.info(f"Created Cloud Task for YouTube video {video.id}")
        except CloudTasksError as e:
            logger.error(f"Cloud Task creation failed: {str(e)}")
            video.status = VideoStatus.failed
            await db.commit()
            raise HTTPException(status_code=500, detail=f"Failed to queue video processing: {str(e)}")

        return YouTubeSubmitResponse(
            id=video.id,
            youtube_url=request.url,
            title=None,  # Title will be set after download
            status=video.status,
            source_type=video.source_type,
            status_url=f"/api/videos/{video.id}/status"
        )

    except Exception as e:
        logger.error(f"Unexpected error processing YouTube video: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while processing the YouTube video: {str(e)}"
        )


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Check processing status of a video."""
    result = await db.execute(
        select(Video).filter(Video.id == video_id, Video.user_id == user_id, Video.deleted_at.is_(None))
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return VideoStatusResponse(
        id=video.id,
        status=video.status,
        uploaded_at=video.uploaded_at,
        duration_seconds=video.duration_seconds,
        title=video.title
    )


@router.get("/{video_id}/transcription", response_model=TranscriptionResponse)
async def get_transcription(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Retrieve completed transcription for a video."""
    result = await db.execute(
        select(Video).filter(Video.id == video_id, Video.user_id == user_id, Video.deleted_at.is_(None))
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    result = await db.execute(select(Transcription).filter(Transcription.video_id == video_id))
    transcription = result.scalar_one_or_none()

    if not transcription:
        if video.status in [VideoStatus.uploading, VideoStatus.uploaded, VideoStatus.processing]:
            raise HTTPException(status_code=404, detail="Transcription not ready yet")
        raise HTTPException(status_code=404, detail="Transcription not found")

    if video.status == VideoStatus.failed:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {transcription.error_message}"
        )

    # Convert JSONB dict back to NotesData Pydantic object
    notes_object = None
    if transcription.notes and isinstance(transcription.notes, dict):
        notes_object = NotesData(**transcription.notes)

    return TranscriptionResponse(
        video_id=transcription.video_id,
        transcript_text=transcription.transcript_text,
        transcript_segments=transcription.transcript_segments,
        model_used=transcription.model_used,
        processing_time=transcription.processing_time,
        created_at=transcription.created_at,
        error_message=transcription.error_message,
        audio_size=transcription.audio_size,
        notes=notes_object
    )


@router.get("", response_model=VideoListResponse)
async def list_videos(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """List all uploaded videos with note summaries for the current user."""
    # Join videos with transcriptions to get note summaries, filter by user_id and exclude soft-deleted
    result = await db.execute(
        select(Video, Transcription)
        .outerjoin(Transcription, Video.id == Transcription.video_id)
        .filter(Video.user_id == user_id, Video.deleted_at.is_(None))
        .order_by(Video.uploaded_at.desc())
    )
    rows = result.all()

    videos_list = []
    for video, transcription in rows:
        note_summary = None
        key_points_count = None
        takeaways_count = None
        tags_count = None
        quotes_count = None

        if transcription and transcription.notes:
            # Handle both dict and string cases
            notes_data = transcription.notes if isinstance(transcription.notes, dict) else None
            if notes_data:
                note_summary = notes_data.get('summary')
                key_points_count = len(notes_data.get('key_points', []))
                takeaways_count = len(notes_data.get('takeaways', []))
                tags_count = len(notes_data.get('tags', []))
                quotes_count = len(notes_data.get('quotes', []))

        videos_list.append(VideoListItem(
            id=video.id,
            filename=video.filename,
            status=video.status,
            uploaded_at=video.uploaded_at,
            note_summary=note_summary,
            key_points_count=key_points_count,
            takeaways_count=takeaways_count,
            tags_count=tags_count,
            quotes_count=quotes_count
        ))

    return VideoListResponse(videos=videos_list)


@router.patch("/{video_id}", response_model=VideoStatusResponse)
async def update_video(
    video_id: UUID,
    update_data: VideoUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Update video metadata (e.g., title)."""
    result = await db.execute(
        select(Video).filter(Video.id == video_id, Video.user_id == user_id, Video.deleted_at.is_(None))
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Update only provided fields
    if update_data.title is not None:
        video.title = update_data.title

    await db.commit()
    await db.refresh(video)

    return VideoStatusResponse(
        id=video.id,
        status=video.status,
        uploaded_at=video.uploaded_at,
        duration_seconds=video.duration_seconds,
        title=video.title
    )


@router.get("/{video_id}/stream", response_model=VideoStreamResponse)
async def get_video_stream(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """
    Get streaming URL for a video (YouTube embed or HLS).

    For YouTube videos: Returns YouTube video ID immediately (no HLS generation).
    For uploaded videos: Returns presigned HLS URL if ready, or triggers generation.
    Client should poll this endpoint when status is 'generating'.
    """
    # Validate user owns video and it's not deleted
    result = await db.execute(
        select(Video).filter(Video.id == video_id, Video.user_id == user_id, Video.deleted_at.is_(None))
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Video must be completed before streaming
    if video.status != VideoStatus.completed:
        raise HTTPException(
            status_code=400,
            detail=f"Video is not ready for streaming. Current status: {video.status}"
        )

    # YouTube videos: Return YouTube video ID immediately (no HLS generation needed)
    if video.source_type == SourceType.youtube and video.youtube_url:
        try:
            yt_video_id = extract_video_id(video.youtube_url)
            return VideoStreamResponse(
                status="ready",
                source_type="youtube",
                youtube_video_id=yt_video_id,
                youtube_url=video.youtube_url,
                hls_url=None,
                retry_after=None,
                error_message=None
            )
        except Exception as e:
            logger.error(f"Failed to extract YouTube video ID for video {video_id}: {str(e)}")
            return VideoStreamResponse(
                status="failed",
                source_type="youtube",
                youtube_video_id=None,
                youtube_url=video.youtube_url,
                hls_url=None,
                retry_after=None,
                error_message=f"Invalid YouTube URL: {str(e)}"
            )

    # Uploaded videos: Direct video streaming via presigned URL
    # For now, skip HLS and use direct MP4 streaming which works with presigned URLs
    try:
        from app.services.r2_service import get_r2_client
        client = get_r2_client()

        # Generate presigned URL for direct video access (expires in 1 hour)
        video_url = client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.r2_bucket_name,
                'Key': video.r2_key
            },
            ExpiresIn=3600
        )

        logger.info(f"Generated direct video URL for {video_id}")

        return VideoStreamResponse(
            status="ready",
            source_type="upload",
            hls_url=video_url,  # Using hls_url field for direct video URL
            youtube_video_id=None,
            youtube_url=None,
            retry_after=None,
            error_message=None
        )
    except Exception as e:
        logger.error(f"Failed to generate video URL for {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate streaming URL")

@router.delete("/{video_id}", response_model=VideoDeleteResponse)
async def delete_video_endpoint(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """
    Delete a video and all associated resources.

    - Deletes video file from R2 storage
    - Deletes HLS files from R2 if they exist
    - Soft deletes database record (sets deleted_at timestamp)
    - Cascade deletion handles related Transcription automatically
    """
    # Validate user owns video
    result = await db.execute(
        select(Video).filter(Video.id == video_id, Video.user_id == user_id, Video.deleted_at.is_(None))
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        # Delete video file from R2
        if video.r2_key:
            try:
                delete_video(video.r2_key)
                logger.info(f"Deleted video from R2: {video.r2_key}")
            except R2Error as e:
                logger.warning(f"Failed to delete video from R2: {str(e)}")
                # Continue with soft delete even if R2 deletion fails

        # Delete HLS files from R2 if they exist
        if video.hls_playlist_key:
            try:
                # Extract HLS directory prefix from playlist key
                # Format: "videos/user_id/video_id_hls/playlist.m3u8" -> "videos/user_id/video_id_hls"
                hls_prefix = "/".join(video.hls_playlist_key.split("/")[:-1])
                delete_hls_directory(hls_prefix)
                logger.info(f"Deleted HLS files from R2: {hls_prefix}")
            except R2Error as e:
                logger.warning(f"Failed to delete HLS files from R2: {str(e)}")
                # Continue with soft delete even if HLS deletion fails

        # Soft delete video record
        video.deleted_at = datetime.utcnow()
        await db.commit()

        logger.info(f"Soft deleted video {video_id} for user {user_id}")

        return VideoDeleteResponse(
            id=video.id,
            deleted=True,
            message="Video and associated resources deleted successfully"
        )

    except Exception as e:
        logger.error(f"Unexpected error deleting video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete video")


async def _generate_hls_background(video_id: str, r2_key: str, user_id: str):
    """Background task to generate HLS for a video."""
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"Starting HLS generation for video {video_id}")

            # Generate HLS (this is CPU-bound, runs synchronously)
            playlist_key = generate_hls_for_video(
                UUID(video_id),
                r2_key,
                user_id
            )

            # Update video record
            result = await db.execute(
                select(Video).filter(Video.id == UUID(video_id))
            )
            video = result.scalar_one_or_none()

            if video:
                video.hls_status = HlsStatus.ready
                video.hls_playlist_key = playlist_key
                video.hls_generated_at = datetime.utcnow()
                video.hls_error_message = None
                await db.commit()

                logger.info(f"HLS generation completed for video {video_id}")

        except HlsGenerationError as e:
            logger.error(f"HLS generation failed for video {video_id}: {str(e)}")

            # Update video with error
            result = await db.execute(
                select(Video).filter(Video.id == UUID(video_id))
            )
            video = result.scalar_one_or_none()

            if video:
                video.hls_status = HlsStatus.failed
                video.hls_error_message = str(e)
                await db.commit()

        except Exception as e:
            logger.error(f"Unexpected error during HLS generation for video {video_id}: {str(e)}")

            result = await db.execute(
                select(Video).filter(Video.id == UUID(video_id))
            )
            video = result.scalar_one_or_none()

            if video:
                video.hls_status = HlsStatus.failed
                video.hls_error_message = f"Unexpected error: {str(e)}"
                await db.commit()
