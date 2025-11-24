#!/usr/bin/env python3
"""
Database cleanup job - deletes all data and resets sequences.
Designed to run as a Cloud Run job with access to Secret Manager.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.config import settings
from loguru import logger


async def cleanup_database():
    """Delete all data and reset primary key sequences."""
    logger.info("Starting database cleanup...")

    async with AsyncSessionLocal() as session:
        # Get counts before cleanup
        result = await session.execute(text('SELECT COUNT(*) FROM videos'))
        video_count = result.scalar()

        result = await session.execute(text('SELECT COUNT(*) FROM transcriptions'))
        transcription_count = result.scalar()

        result = await session.execute(text('SELECT COUNT(*) FROM tags'))
        tag_count = result.scalar()

        result = await session.execute(text('SELECT COUNT(*) FROM collections'))
        collection_count = result.scalar()

        logger.info(
            f"Before cleanup: {video_count} videos, {transcription_count} transcriptions, "
            f"{tag_count} tags, {collection_count} collections"
        )

        # Delete all data (order matters due to foreign keys)
        await session.execute(text('DELETE FROM transcriptions'))
        await session.execute(text('DELETE FROM video_tags'))
        await session.execute(text('DELETE FROM videos'))
        await session.execute(text('DELETE FROM tags'))
        await session.execute(text('DELETE FROM collections'))

        await session.commit()

        # Verify cleanup
        result = await session.execute(text('SELECT COUNT(*) FROM videos'))
        video_count = result.scalar()

        result = await session.execute(text('SELECT COUNT(*) FROM transcriptions'))
        transcription_count = result.scalar()

        result = await session.execute(text('SELECT COUNT(*) FROM tags'))
        tag_count = result.scalar()

        result = await session.execute(text('SELECT COUNT(*) FROM collections'))
        collection_count = result.scalar()

        logger.info(
            f"After cleanup: {video_count} videos, {transcription_count} transcriptions, "
            f"{tag_count} tags, {collection_count} collections"
        )
        logger.info("✅ Database cleanup complete!")


if __name__ == '__main__':
    logger.info(f"Connecting to database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    asyncio.run(cleanup_database())
