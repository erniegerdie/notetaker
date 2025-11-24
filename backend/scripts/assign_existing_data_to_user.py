"""
Migration script to assign existing videos, collections, and tags to a user.

This script should be run AFTER the user_id columns have been added via Alembic migration.
It assigns all records with NULL user_id to a specified user ID.

Usage:
    uv run python scripts/assign_existing_data_to_user.py <user_uuid>

Example:
    uv run python scripts/assign_existing_data_to_user.py 550e8400-e29b-41d4-a716-446655440000
"""

import asyncio
import sys
from sqlalchemy import update
from app.database import AsyncSessionLocal
from app.models import Video, Collection, Tag
from loguru import logger


async def assign_data_to_user(user_id: str):
    """Assign all existing NULL user_id records to the specified user."""

    async with AsyncSessionLocal() as session:
        try:
            # Update videos
            videos_result = await session.execute(
                update(Video)
                .where(Video.user_id.is_(None))
                .values(user_id=user_id)
            )
            videos_count = videos_result.rowcount

            # Update collections
            collections_result = await session.execute(
                update(Collection)
                .where(Collection.user_id.is_(None))
                .values(user_id=user_id)
            )
            collections_count = collections_result.rowcount

            # Update tags
            tags_result = await session.execute(
                update(Tag)
                .where(Tag.user_id.is_(None))
                .values(user_id=user_id)
            )
            tags_count = tags_result.rowcount

            await session.commit()

            logger.info(f"✅ Data migration completed:")
            logger.info(f"   - Videos assigned: {videos_count}")
            logger.info(f"   - Collections assigned: {collections_count}")
            logger.info(f"   - Tags assigned: {tags_count}")
            logger.info(f"   - Assigned to user: {user_id}")

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Migration failed: {str(e)}")
            raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run python scripts/assign_existing_data_to_user.py <user_uuid>")
        print("\nExample:")
        print("  uv run python scripts/assign_existing_data_to_user.py 550e8400-e29b-41d4-a716-446655440000")
        sys.exit(1)

    user_id = sys.argv[1]

    # Validate UUID format (basic check)
    if len(user_id) != 36:
        print("❌ Error: User ID must be a valid UUID (36 characters)")
        sys.exit(1)

    print(f"\n🔄 Assigning existing data to user: {user_id}")
    print("This will update all videos, collections, and tags with NULL user_id")
    confirm = input("Continue? (yes/no): ")

    if confirm.lower() != "yes":
        print("Migration cancelled")
        sys.exit(0)

    asyncio.run(assign_data_to_user(user_id))
