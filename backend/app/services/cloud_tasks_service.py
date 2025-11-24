"""Google Cloud Tasks service for managing video processing jobs."""
import json
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2, duration_pb2
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from app.config import settings


class CloudTasksError(Exception):
    """Exception raised when Cloud Tasks operations fail."""
    pass


def create_video_processing_task(
    video_id: str,
    r2_key: str,
    user_id: str,
    delay_seconds: int = 0
) -> str:
    """
    Create a Cloud Task to process a video asynchronously.

    Args:
        video_id: Video database ID
        r2_key: R2 storage key for the video file
        user_id: User ID who owns the video
        delay_seconds: Optional delay before task execution

    Returns:
        Task name (full resource path)

    Raises:
        CloudTasksError: If task creation fails
    """
    try:
        # Create Cloud Tasks client
        client = tasks_v2.CloudTasksClient()

        # Construct the queue path
        queue_path = client.queue_path(
            settings.gcp_project_id,
            settings.gcp_region,
            settings.cloud_tasks_queue
        )

        # Build task payload
        task_payload = {
            "video_id": video_id,
            "r2_key": r2_key,
            "user_id": user_id
        }

        # Construct the task
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{settings.worker_service_url}/process-video",
                "headers": {
                    "Content-Type": "application/json",
                },
                "body": json.dumps(task_payload).encode(),
                "oidc_token": {
                    "service_account_email": settings.cloud_tasks_service_account
                }
            },
            # Set dispatch deadline to maximum allowed (30 minutes)
            # Cloud Tasks maximum is 1800s (30 min) for HTTP targets
            "dispatch_deadline": duration_pb2.Duration(seconds=1800)
        }

        # Add delay if specified
        if delay_seconds > 0:
            schedule_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(schedule_time)
            task["schedule_time"] = timestamp

        # Create the task
        response = client.create_task(
            request={"parent": queue_path, "task": task}
        )

        logger.info(
            f"Created Cloud Task for video {video_id}: {response.name}"
        )
        return response.name

    except Exception as e:
        error_msg = f"Failed to create Cloud Task for video {video_id}: {str(e)}"
        logger.error(error_msg)
        raise CloudTasksError(error_msg) from e


def delete_task(task_name: str) -> None:
    """
    Delete a Cloud Task.

    Args:
        task_name: Full task resource name

    Raises:
        CloudTasksError: If task deletion fails
    """
    try:
        client = tasks_v2.CloudTasksClient()
        client.delete_task(name=task_name)
        logger.info(f"Deleted Cloud Task: {task_name}")
    except Exception as e:
        error_msg = f"Failed to delete Cloud Task {task_name}: {str(e)}"
        logger.error(error_msg)
        raise CloudTasksError(error_msg) from e


def get_task_status(task_name: str) -> Optional[dict]:
    """
    Get the status of a Cloud Task.

    Args:
        task_name: Full task resource name

    Returns:
        Task details dict or None if not found

    Raises:
        CloudTasksError: If status check fails
    """
    try:
        client = tasks_v2.CloudTasksClient()
        task = client.get_task(name=task_name)

        return {
            "name": task.name,
            "schedule_time": task.schedule_time,
            "dispatch_count": task.dispatch_count,
            "response_count": task.response_count,
            "first_attempt": task.first_attempt,
            "last_attempt": task.last_attempt,
        }
    except Exception as e:
        logger.warning(f"Could not get task status for {task_name}: {str(e)}")
        return None
