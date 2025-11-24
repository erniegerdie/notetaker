#!/usr/bin/env python3
"""
R2 Bucket Cleanup Script

Deletes all objects and aborts all multipart uploads in the configured R2 bucket.
Use with caution - this is a destructive operation!

Usage:
    # Dry run (default - shows what would be deleted without deleting)
    uv run python scripts/cleanup_r2_bucket.py

    # Actually delete everything (requires --confirm flag)
    uv run python scripts/cleanup_r2_bucket.py --confirm
"""
import sys
from pathlib import Path
from typing import List, Dict, Any
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from botocore.exceptions import ClientError
from loguru import logger

from app.services.r2_service import get_r2_client, R2Error
from app.config import settings


def list_all_objects(client, bucket_name: str) -> List[Dict[str, Any]]:
    """
    List all objects in the bucket using pagination.

    Args:
        client: boto3 S3 client
        bucket_name: Name of the bucket

    Returns:
        List of object dictionaries with Key and Size
    """
    objects = []
    continuation_token = None

    logger.info(f"Scanning bucket: {bucket_name}")

    while True:
        try:
            if continuation_token:
                response = client.list_objects_v2(
                    Bucket=bucket_name,
                    ContinuationToken=continuation_token
                )
            else:
                response = client.list_objects_v2(Bucket=bucket_name)

            if 'Contents' in response:
                batch = response['Contents']
                objects.extend(batch)
                logger.info(f"  Found {len(batch)} objects (total: {len(objects)})")
            else:
                logger.info(f"  No objects found in bucket")

            if not response.get('IsTruncated'):
                break

            continuation_token = response.get('NextContinuationToken')

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Error listing objects [{error_code}]: {error_msg}")
            raise

    return objects


def list_multipart_uploads(client, bucket_name: str) -> List[Dict[str, Any]]:
    """
    List all incomplete multipart uploads.

    Args:
        client: boto3 S3 client
        bucket_name: Name of the bucket

    Returns:
        List of multipart upload dictionaries
    """
    uploads = []
    key_marker = None
    upload_id_marker = None

    logger.info(f"Scanning for multipart uploads in: {bucket_name}")

    while True:
        try:
            params = {'Bucket': bucket_name}
            if key_marker:
                params['KeyMarker'] = key_marker
            if upload_id_marker:
                params['UploadIdMarker'] = upload_id_marker

            response = client.list_multipart_uploads(**params)

            if 'Uploads' in response:
                batch = response['Uploads']
                uploads.extend(batch)
                logger.info(f"  Found {len(batch)} multipart uploads (total: {len(uploads)})")
            else:
                logger.info(f"  No multipart uploads found")

            if not response.get('IsTruncated'):
                break

            key_marker = response.get('NextKeyMarker')
            upload_id_marker = response.get('NextUploadIdMarker')

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Error listing multipart uploads [{error_code}]: {error_msg}")
            raise

    return uploads


def delete_objects(client, bucket_name: str, objects: List[Dict[str, Any]], dry_run: bool = True) -> int:
    """
    Delete objects in batches (max 1000 per batch as per S3 API limit).

    Args:
        client: boto3 S3 client
        bucket_name: Name of the bucket
        objects: List of objects to delete
        dry_run: If True, only show what would be deleted

    Returns:
        Number of objects deleted
    """
    if not objects:
        logger.info("No objects to delete")
        return 0

    total_size = sum(obj.get('Size', 0) for obj in objects)
    logger.info(f"{'[DRY RUN] Would delete' if dry_run else 'Deleting'} {len(objects)} objects ({total_size / (1024**3):.2f} GB)")

    if dry_run:
        # Show sample of objects that would be deleted
        sample_size = min(10, len(objects))
        logger.info(f"Sample of objects (showing {sample_size} of {len(objects)}):")
        for obj in objects[:sample_size]:
            logger.info(f"  - {obj['Key']} ({obj.get('Size', 0) / (1024**2):.2f} MB)")
        return 0

    deleted_count = 0
    batch_size = 1000  # S3 API limit

    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]

        try:
            response = client.delete_objects(
                Bucket=bucket_name,
                Delete={
                    'Objects': [{'Key': obj['Key']} for obj in batch],
                    'Quiet': False
                }
            )

            deleted = len(response.get('Deleted', []))
            deleted_count += deleted

            logger.info(f"Deleted batch: {deleted} objects (progress: {deleted_count}/{len(objects)})")

            if 'Errors' in response:
                for error in response['Errors']:
                    logger.error(f"  Failed to delete {error['Key']}: {error['Message']}")

        except ClientError as e:
            logger.error(f"Error deleting batch: {e}")
            raise

    return deleted_count


def abort_multipart_uploads(client, bucket_name: str, uploads: List[Dict[str, Any]], dry_run: bool = True) -> int:
    """
    Abort incomplete multipart uploads.

    Args:
        client: boto3 S3 client
        bucket_name: Name of the bucket
        uploads: List of multipart uploads to abort
        dry_run: If True, only show what would be aborted

    Returns:
        Number of uploads aborted
    """
    if not uploads:
        logger.info("No multipart uploads to abort")
        return 0

    logger.info(f"{'[DRY RUN] Would abort' if dry_run else 'Aborting'} {len(uploads)} multipart uploads")

    if dry_run:
        # Show sample of uploads that would be aborted
        sample_size = min(10, len(uploads))
        logger.info(f"Sample of multipart uploads (showing {sample_size} of {len(uploads)}):")
        for upload in uploads[:sample_size]:
            logger.info(f"  - {upload['Key']} (UploadId: {upload['UploadId']})")
        return 0

    aborted_count = 0

    for upload in uploads:
        try:
            client.abort_multipart_upload(
                Bucket=bucket_name,
                Key=upload['Key'],
                UploadId=upload['UploadId']
            )
            aborted_count += 1
            logger.info(f"Aborted: {upload['Key']} (progress: {aborted_count}/{len(uploads)})")

        except ClientError as e:
            logger.error(f"Error aborting {upload['Key']}: {e}")

    return aborted_count


def cleanup_bucket(dry_run: bool = True) -> bool:
    """
    Main cleanup function.

    Args:
        dry_run: If True, only show what would be cleaned up

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("=" * 70)
        logger.info(f"R2 Bucket Cleanup - {'DRY RUN MODE' if dry_run else 'DELETION MODE'}")
        logger.info("=" * 70)
        logger.info(f"Bucket: {settings.r2_bucket_name}")
        logger.info(f"Endpoint: {settings.r2_endpoint_url}")

        # Validate endpoint URL format
        if settings.r2_endpoint_url.endswith(f"/{settings.r2_bucket_name}"):
            logger.warning("⚠️  WARNING: R2_ENDPOINT_URL should NOT include the bucket name!")
            logger.warning(f"   Current: {settings.r2_endpoint_url}")
            logger.warning(f"   Should be: {settings.r2_endpoint_url.replace(f'/{settings.r2_bucket_name}', '')}")
            logger.warning("   This may cause connection issues. Please update your .env file.")
            logger.warning("")

        if not dry_run:
            logger.warning("⚠️  THIS WILL PERMANENTLY DELETE ALL DATA IN THE BUCKET!")

        # Get R2 client
        client = get_r2_client()

        # List all objects
        logger.info("\n📦 Step 1: Listing objects...")
        objects = list_all_objects(client, settings.r2_bucket_name)

        # List multipart uploads
        logger.info("\n📤 Step 2: Listing multipart uploads...")
        uploads = list_multipart_uploads(client, settings.r2_bucket_name)

        # Delete objects
        logger.info("\n🗑️  Step 3: Deleting objects...")
        deleted_objects = delete_objects(client, settings.r2_bucket_name, objects, dry_run)

        # Abort multipart uploads
        logger.info("\n🚫 Step 4: Aborting multipart uploads...")
        aborted_uploads = abort_multipart_uploads(client, settings.r2_bucket_name, uploads, dry_run)

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("Summary:")
        logger.info(f"  Objects found: {len(objects)}")
        logger.info(f"  Multipart uploads found: {len(uploads)}")

        if dry_run:
            logger.info(f"  [DRY RUN] Would delete: {len(objects)} objects")
            logger.info(f"  [DRY RUN] Would abort: {len(uploads)} uploads")
            logger.info("\n💡 Run with --confirm flag to actually delete")
        else:
            logger.info(f"  ✅ Objects deleted: {deleted_objects}")
            logger.info(f"  ✅ Uploads aborted: {aborted_uploads}")

            if deleted_objects + aborted_uploads == len(objects) + len(uploads):
                logger.info("\n✅ Bucket cleanup complete!")
            else:
                logger.warning("\n⚠️  Some items may not have been cleaned up - check logs above")

        logger.info("=" * 70)

        return True

    except R2Error as e:
        logger.error(f"\n❌ R2 configuration error: {e}")
        return False
    except ClientError as e:
        logger.error(f"\n❌ AWS/R2 client error: {e}")
        return False
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Clean up R2 bucket by deleting all objects and aborting multipart uploads',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (shows what would be deleted)
  uv run python scripts/cleanup_r2_bucket.py

  # Actually delete everything (requires confirmation)
  uv run python scripts/cleanup_r2_bucket.py --confirm
        """
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Actually delete data (without this flag, runs in dry-run mode)'
    )

    args = parser.parse_args()

    # Run cleanup
    success = cleanup_bucket(dry_run=not args.confirm)

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
