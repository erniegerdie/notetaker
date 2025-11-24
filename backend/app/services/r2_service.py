"""Cloudflare R2 storage service for video uploads."""
import os
import uuid
import tempfile
from pathlib import Path
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError
from loguru import logger

from app.config import settings


class R2Error(Exception):
    """Exception raised when R2 operations fail."""
    pass


def get_r2_client():
    """
    Create and return boto3 S3 client configured for Cloudflare R2.

    Returns:
        boto3 S3 client instance

    Raises:
        R2Error: If R2 configuration is missing or invalid
    """
    if not all([
        settings.r2_endpoint_url,
        settings.r2_access_key_id,
        settings.r2_secret_access_key,
        settings.r2_bucket_name
    ]):
        raise R2Error(
            "R2 configuration incomplete. Required: R2_ENDPOINT_URL, "
            "R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME"
        )

    try:
        client = boto3.client(
            's3',
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name='auto'  # R2 uses 'auto' for region
        )
        return client
    except Exception as e:
        raise R2Error(f"Failed to create R2 client: {str(e)}")


def upload_video(
    file_obj: BinaryIO,
    filename: str,
    user_id: Optional[str] = None,
    content_type: str = "video/mp4"
) -> tuple[str, int]:
    """
    Upload video file to R2 bucket.

    Args:
        file_obj: File object to upload (e.g., UploadFile.file or open file)
        filename: Original filename
        user_id: Optional user ID for organizing files
        content_type: MIME type of the video

    Returns:
        Tuple of (r2_key, file_size_bytes)

    Raises:
        R2Error: If upload fails
    """
    try:
        client = get_r2_client()

        # Generate unique R2 key
        file_ext = Path(filename).suffix
        unique_id = uuid.uuid4()

        if user_id:
            r2_key = f"videos/{user_id}/{unique_id}{file_ext}"
        else:
            r2_key = f"videos/{unique_id}{file_ext}"

        logger.info(f"Uploading video to R2: {r2_key}")

        # Upload file to R2
        client.upload_fileobj(
            file_obj,
            settings.r2_bucket_name,
            r2_key,
            ExtraArgs={
                'ContentType': content_type,
                'Metadata': {
                    'original_filename': filename
                }
            }
        )

        # Get file size
        response = client.head_object(
            Bucket=settings.r2_bucket_name,
            Key=r2_key
        )
        file_size = response['ContentLength']

        logger.info(f"Upload complete: {r2_key} ({file_size} bytes)")

        return r2_key, file_size

    except ClientError as e:
        error_msg = f"R2 upload failed: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during R2 upload: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)


def upload_local_file(
    local_path: str,
    user_id: Optional[str] = None,
    content_type: str = "video/mp4"
) -> tuple[str, int]:
    """
    Upload local video file to R2 bucket.

    Args:
        local_path: Path to local file
        user_id: Optional user ID for organizing files
        content_type: MIME type of the video

    Returns:
        Tuple of (r2_key, file_size_bytes)

    Raises:
        R2Error: If file doesn't exist or upload fails
    """
    if not os.path.exists(local_path):
        raise R2Error(f"Local file not found: {local_path}")

    try:
        with open(local_path, 'rb') as f:
            filename = Path(local_path).name
            return upload_video(f, filename, user_id, content_type)
    except R2Error:
        raise
    except Exception as e:
        raise R2Error(f"Failed to upload local file: {str(e)}")


def download_video(r2_key: str, destination_path: Optional[str] = None) -> tuple[str, int]:
    """
    Download video from R2 to local temporary file.

    Args:
        r2_key: R2 object key
        destination_path: Optional destination path (uses temp file if not provided)

    Returns:
        Tuple of (local_file_path, file_size_bytes)

    Raises:
        R2Error: If download fails
    """
    try:
        client = get_r2_client()

        # Create destination path if not provided
        if not destination_path:
            file_ext = Path(r2_key).suffix
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_ext,
                prefix="r2_download_"
            )
            destination_path = temp_file.name
            temp_file.close()

        logger.info(f"Downloading from R2: {r2_key} → {destination_path}")

        # Download file
        client.download_file(
            settings.r2_bucket_name,
            r2_key,
            destination_path
        )

        # Get file size
        file_size = os.path.getsize(destination_path)

        logger.info(f"Download complete: {destination_path} ({file_size} bytes)")

        return destination_path, file_size

    except ClientError as e:
        if e.response.get('Error', {}).get('Code') == 'NoSuchKey':
            raise R2Error(f"Video not found in R2: {r2_key}")
        error_msg = f"R2 download failed: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during R2 download: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)


def delete_video(r2_key: str) -> None:
    """
    Delete video from R2 bucket.

    Args:
        r2_key: R2 object key to delete

    Raises:
        R2Error: If deletion fails
    """
    try:
        client = get_r2_client()

        logger.info(f"Deleting from R2: {r2_key}")

        client.delete_object(
            Bucket=settings.r2_bucket_name,
            Key=r2_key
        )

        logger.info(f"Deleted from R2: {r2_key}")

    except ClientError as e:
        error_msg = f"R2 deletion failed: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during R2 deletion: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)


def get_video_url(r2_key: str, expires_in: int = 3600) -> str:
    """
    Generate presigned URL for video access.

    Args:
        r2_key: R2 object key
        expires_in: URL expiration time in seconds (default 1 hour)

    Returns:
        Presigned URL for video access

    Raises:
        R2Error: If URL generation fails
    """
    try:
        client = get_r2_client()

        # If public URL is configured, use it
        if settings.r2_public_url:
            return f"{settings.r2_public_url.rstrip('/')}/{r2_key}"

        # Otherwise generate presigned URL
        url = client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.r2_bucket_name,
                'Key': r2_key
            },
            ExpiresIn=expires_in
        )

        return url

    except ClientError as e:
        error_msg = f"Failed to generate R2 URL: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error generating R2 URL: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)


def generate_presigned_upload_url(
    r2_key: str,
    content_type: str = "video/mp4",
    expires_in: int = 3600
) -> str:
    """
    Generate presigned URL for uploading to R2.

    Args:
        r2_key: R2 object key where file will be stored
        content_type: MIME type of the file
        expires_in: URL expiration time in seconds (default 1 hour)

    Returns:
        Presigned URL for PUT upload

    Raises:
        R2Error: If URL generation fails
    """
    try:
        client = get_r2_client()

        # Generate presigned URL for PUT operation
        url = client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.r2_bucket_name,
                'Key': r2_key,
                'ContentType': content_type
            },
            ExpiresIn=expires_in
        )

        logger.info(f"Generated presigned upload URL for {r2_key} (expires in {expires_in}s)")

        return url

    except ClientError as e:
        error_msg = f"Failed to generate presigned upload URL: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error generating presigned upload URL: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)


def verify_r2_object_exists(r2_key: str) -> bool:
    """
    Verify that an object exists in R2.

    Args:
        r2_key: R2 object key to check

    Returns:
        True if object exists

    Raises:
        R2Error: If object does not exist or check fails
    """
    try:
        client = get_r2_client()

        # Use head_object to check existence without downloading
        client.head_object(
            Bucket=settings.r2_bucket_name,
            Key=r2_key
        )

        logger.info(f"Verified R2 object exists: {r2_key}")
        return True

    except ClientError as e:
        if e.response.get('Error', {}).get('Code') == 'NoSuchKey':
            raise R2Error(f"Object not found in R2: {r2_key}")
        error_msg = f"Failed to verify R2 object existence: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error verifying R2 object: {str(e)}"
        logger.error(error_msg)
        raise R2Error(error_msg)


def cleanup_temp_file(file_path: str) -> None:
    """
    Delete temporary downloaded file.

    Args:
        file_path: Path to temporary file
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temp file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up temp file {file_path}: {str(e)}")
