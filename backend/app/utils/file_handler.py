import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import settings
from app.services.r2_service import upload_video, R2Error


def validate_video_file(file: UploadFile) -> None:
    """Validate uploaded video file format and size."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in settings.allowed_formats_list:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed formats: {settings.allowed_video_formats}"
        )


async def save_upload_file(file: UploadFile) -> tuple[str, int]:
    """
    Save uploaded file to disk.

    Returns:
        tuple: (file_path, file_size)
    """
    # Create uploads directory if it doesn't exist
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = upload_dir / unique_filename

    # Write file to disk
    file_size = 0
    with open(file_path, "wb") as f:
        while chunk := await file.read(8192):
            file_size += len(chunk)
            if file_size > settings.max_file_size_bytes:
                # Clean up partial file
                f.close()
                os.remove(file_path)
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
                )
            f.write(chunk)

    return str(file_path), file_size


async def save_upload_to_r2(file: UploadFile, user_id: str = None) -> tuple[str, int]:
    """
    Upload file directly to R2 storage.

    Args:
        file: FastAPI UploadFile instance
        user_id: Optional user ID for organizing files in R2

    Returns:
        tuple: (r2_key, file_size)

    Raises:
        HTTPException: If upload fails
    """
    try:
        # Determine content type from file extension
        file_ext = file.filename.split(".")[-1].lower()
        content_type_map = {
            'mp4': 'video/mp4',
            'avi': 'video/x-msvideo',
            'mov': 'video/quicktime',
            'mkv': 'video/x-matroska'
        }
        content_type = content_type_map.get(file_ext, 'video/mp4')

        # Upload to R2
        r2_key, file_size = upload_video(
            file.file,
            file.filename,
            user_id=user_id,
            content_type=content_type
        )

        return r2_key, file_size

    except R2Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload to R2: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during upload: {str(e)}"
        )


def delete_file(file_path: str) -> None:
    """Delete file from disk if it exists."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
