#!/usr/bin/env python3
"""
R2 Bucket Streaming Cleanup Script

Deletes objects and aborts multipart uploads in batches without pre-scanning.
Processes one page at a time for faster cleanup of large buckets.

Usage:
    # Dry run (default - shows first page without deleting)
    uv run python scripts/cleanup_r2_bucket_streaming.py

    # Actually delete everything (requires --confirm flag)
    uv run python scripts/cleanup_r2_bucket_streaming.py --confirm

    # Limit number of objects to delete
    uv run python scripts/cleanup_r2_bucket_streaming.py --confirm --limit 100
"""
import sys
import os
from pathlib import Path
from typing import Optional
import argparse
import boto3

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from botocore.exceptions import ClientError
from loguru import logger

from app.config import settings


R2_ADMIN_TOKEN = "hKp5K9k_bxoEWqnJtVnaskl1pxCUJIGMLtxigrtu"
R2_ADMIN_KEY_ID = "d23be321466e903d6ab0ddaf77dd5583"
R2_ADMIN_SECRET_ACCESS_KEY = (
    "168b62212e6177b27735a84fc8c385e09b237c97b1f88ec04b286efd38f32139"
)


class R2Error(Exception):
    """Exception raised when R2 operations fail."""

    pass


def get_r2_admin_client():
    """
    Create boto3 S3 client using admin credentials (defined inline).

    Returns:
        boto3 S3 client instance

    Raises:
        R2Error: If configuration is missing
    """
    # ADMIN CREDENTIALS - Replace these with your actual admin credentials
    admin_key_id = "d23be321466e903d6ab0ddaf77dd5583"
    admin_secret = "168b62212e6177b27735a84fc8c385e09b237c97b1f88ec04b286efd38f32139"

    # Hardcoded endpoint (override settings to avoid /notetaker suffix issue)
    endpoint_url = "https://0b078b76488bd8482030576f1d0b63d6.r2.cloudflarestorage.com"
    bucket_name = "notetaker"

    logger.info(f"Using endpoint: {endpoint_url}")
    logger.info(f"Using bucket: {bucket_name}")

    try:
        from botocore.config import Config

        config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},  # <-- this is the correct place
            connect_timeout=5,
            read_timeout=10,
            retries={"max_attempts": 2},
        )

        client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
        )
        # Skip connection test - go straight to operations
        logger.info("✅ Client created, will test on first operation")

        def get_first_object():

            resp = client.list_objects_v2(
                Bucket=bucket_name,
                MaxKeys=1,
            )

            contents = resp.get("Contents")
            if not contents:
                print("Bucket is empty")
                return None

            obj = contents[0]
            print(f"First object key: {obj['Key']}")
            print(f"Size: {obj['Size']} bytes")
            print(f"Last modified: {obj['LastModified']}")

            return obj

        logger.info("Getting first object...")
        get_first_object()

        return client, bucket_name
    except R2Error:
        raise
    except Exception as e:
        raise R2Error(f"Failed to create R2 admin client: {str(e)}")


def cleanup_objects_streaming(
    client, bucket_name: str, dry_run: bool = True, limit: Optional[int] = None
) -> int:
    """
    Delete objects in streaming fashion without pre-scanning.

    Args:
        client: boto3 S3 client
        bucket_name: Name of the bucket
        dry_run: If True, only show what would be deleted
        limit: Optional limit on number of objects to delete

    Returns:
        Number of objects deleted
    """
    deleted_count = 0
    continuation_token = None
    page_num = 0

    logger.info(
        f"{'[DRY RUN] Processing' if dry_run else 'Processing'} objects in streaming mode..."
    )

    while True:
        page_num += 1

        try:
            # List one page at a time
            params = {"Bucket": bucket_name, "MaxKeys": 1000}
            if continuation_token:
                params["ContinuationToken"] = continuation_token

            logger.info(f"\n📄 Page {page_num}: Listing next batch...")
            response = client.list_objects_v2(**params)

            if "Contents" not in response:
                logger.info("  ✅ No more objects found")
                break

            objects = response["Contents"]
            logger.info(f"  Found {len(objects)} objects")

            # Check limit
            if limit and deleted_count + len(objects) > limit:
                objects = objects[: limit - deleted_count]
                logger.info(
                    f"  Limiting to {len(objects)} objects (reaching limit of {limit})"
                )

            # Show sample
            if dry_run or page_num == 1:
                sample_size = min(5, len(objects))
                logger.info(f"  Sample objects:")
                for obj in objects[:sample_size]:
                    logger.info(
                        f"    - {obj['Key']} ({obj.get('Size', 0) / (1024**2):.2f} MB)"
                    )

            if not dry_run:
                # Delete batch
                logger.info(f"  🗑️  Deleting {len(objects)} objects...")
                delete_response = client.delete_objects(
                    Bucket=bucket_name,
                    Delete={
                        "Objects": [{"Key": obj["Key"]} for obj in objects],
                        "Quiet": False,
                    },
                )

                deleted_in_batch = len(delete_response.get("Deleted", []))
                deleted_count += deleted_in_batch
                logger.info(
                    f"  ✅ Deleted {deleted_in_batch} objects (total: {deleted_count})"
                )

                if "Errors" in delete_response:
                    for error in delete_response["Errors"]:
                        logger.error(
                            f"    ❌ Failed: {error['Key']}: {error['Message']}"
                        )
            else:
                logger.info(f"  [DRY RUN] Would delete {len(objects)} objects")
                deleted_count += len(objects)

            # Check if we've hit the limit
            if limit and deleted_count >= limit:
                logger.info(f"\n🎯 Reached limit of {limit} objects")
                break

            # Check if there are more pages
            if not response.get("IsTruncated"):
                logger.info("\n✅ No more pages")
                break

            continuation_token = response.get("NextContinuationToken")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"❌ Error on page {page_num} [{error_code}]: {error_msg}")
            raise

    return deleted_count


def cleanup_multipart_uploads_streaming(
    client, bucket_name: str, dry_run: bool = True, limit: Optional[int] = None
) -> int:
    """
    Abort multipart uploads in streaming fashion.

    Args:
        client: boto3 S3 client
        bucket_name: Name of the bucket
        dry_run: If True, only show what would be aborted
        limit: Optional limit on number of uploads to abort

    Returns:
        Number of uploads aborted
    """
    aborted_count = 0
    key_marker = None
    upload_id_marker = None
    page_num = 0

    logger.info(
        f"{'[DRY RUN] Processing' if dry_run else 'Processing'} multipart uploads..."
    )

    while True:
        page_num += 1

        try:
            # List one page at a time
            params = {"Bucket": bucket_name, "MaxUploads": 1000}
            if key_marker:
                params["KeyMarker"] = key_marker
            if upload_id_marker:
                params["UploadIdMarker"] = upload_id_marker

            logger.info(f"\n📄 Page {page_num}: Listing multipart uploads...")
            response = client.list_multipart_uploads(**params)

            if "Uploads" not in response:
                logger.info("  ✅ No multipart uploads found")
                break

            uploads = response["Uploads"]
            logger.info(f"  Found {len(uploads)} multipart uploads")

            # Check limit
            if limit and aborted_count + len(uploads) > limit:
                uploads = uploads[: limit - aborted_count]
                logger.info(
                    f"  Limiting to {len(uploads)} uploads (reaching limit of {limit})"
                )

            # Show sample
            if dry_run or page_num == 1:
                sample_size = min(5, len(uploads))
                logger.info(f"  Sample uploads:")
                for upload in uploads[:sample_size]:
                    logger.info(
                        f"    - {upload['Key']} (ID: {upload['UploadId'][:16]}...)"
                    )

            if not dry_run:
                # Abort uploads one by one
                logger.info(f"  🚫 Aborting {len(uploads)} uploads...")
                for upload in uploads:
                    try:
                        client.abort_multipart_upload(
                            Bucket=bucket_name,
                            Key=upload["Key"],
                            UploadId=upload["UploadId"],
                        )
                        aborted_count += 1
                    except ClientError as e:
                        logger.error(f"    ❌ Failed to abort {upload['Key']}: {e}")

                logger.info(
                    f"  ✅ Aborted {len(uploads)} uploads (total: {aborted_count})"
                )
            else:
                logger.info(f"  [DRY RUN] Would abort {len(uploads)} uploads")
                aborted_count += len(uploads)

            # Check if we've hit the limit
            if limit and aborted_count >= limit:
                logger.info(f"\n🎯 Reached limit of {limit} uploads")
                break

            # Check if there are more pages
            if not response.get("IsTruncated"):
                logger.info("\n✅ No more pages")
                break

            key_marker = response.get("NextKeyMarker")
            upload_id_marker = response.get("NextUploadIdMarker")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"❌ Error on page {page_num} [{error_code}]: {error_msg}")
            raise

    return aborted_count


def cleanup_bucket_streaming(dry_run: bool = True, limit: Optional[int] = None) -> bool:
    """
    Main streaming cleanup function.

    Args:
        dry_run: If True, only show what would be cleaned up
        limit: Optional limit on items to process

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("=" * 70)
        logger.info(
            f"R2 Bucket Streaming Cleanup - {'DRY RUN MODE' if dry_run else 'DELETION MODE'}"
        )
        logger.info("=" * 70)
        logger.info(f"Bucket: {settings.r2_bucket_name}")
        logger.info(f"Endpoint: {settings.r2_endpoint_url}")
        if limit:
            logger.info(f"Limit: {limit} items per category")

        if not dry_run:
            logger.warning("\n⚠️  THIS WILL PERMANENTLY DELETE DATA IN THE BUCKET!")

        # Get R2 admin client
        logger.info("\n🔑 Using admin credentials")
        client, bucket_name = get_r2_admin_client()

        # Delete objects
        logger.info("\n🗑️  Step 1: Deleting objects (streaming)...")
        deleted_objects = cleanup_objects_streaming(client, bucket_name, dry_run, limit)

        # Abort multipart uploads
        logger.info("\n🚫 Step 2: Aborting multipart uploads (streaming)...")
        aborted_uploads = cleanup_multipart_uploads_streaming(
            client, bucket_name, dry_run, limit
        )

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("Summary:")

        if dry_run:
            logger.info(f"  [DRY RUN] Would delete: {deleted_objects} objects")
            logger.info(f"  [DRY RUN] Would abort: {aborted_uploads} uploads")
            logger.info("\n💡 Run with --confirm flag to actually delete")
        else:
            logger.info(f"  ✅ Objects deleted: {deleted_objects}")
            logger.info(f"  ✅ Uploads aborted: {aborted_uploads}")
            logger.info(f"\n✅ Cleanup complete!")

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
        description="Clean up R2 bucket in streaming mode (processes one page at a time)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (shows first page only)
  uv run python scripts/cleanup_r2_bucket_streaming.py

  # Actually delete everything
  uv run python scripts/cleanup_r2_bucket_streaming.py --confirm

  # Delete only first 100 objects
  uv run python scripts/cleanup_r2_bucket_streaming.py --confirm --limit 100
        """,
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually delete data (without this flag, runs in dry-run mode)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of items to process per category (objects/uploads)",
    )

    args = parser.parse_args()

    # Run cleanup
    success = cleanup_bucket_streaming(dry_run=not args.confirm, limit=args.limit)

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
