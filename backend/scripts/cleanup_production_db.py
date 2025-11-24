#!/usr/bin/env python3
"""
Cleanup production database - delete all videos, transcriptions, and tags.
This script is meant to be run from Cloud Run with proper database credentials.
"""
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal
from loguru import logger

async def cleanup_database():
    """Delete all data from production database."""
    async with AsyncSessionLocal() as session:
        # Get counts before
        result = await session.execute(text('SELECT COUNT(*) FROM videos'))
        video_count = result.scalar()

        result = await session.execute(text('SELECT COUNT(*) FROM transcriptions'))
        transcription_count = result.scalar()

        result = await session.execute(text('SELECT COUNT(*) FROM tags'))
        tag_count = result.scalar()

        logger.info(f'Before cleanup: {video_count} videos, {transcription_count} transcriptions, {tag_count} tags')

        # Delete all (order matters due to foreign keys)
        await session.execute(text('DELETE FROM transcriptions'))
        await session.execute(text('DELETE FROM video_tags'))
        await session.execute(text('DELETE FROM videos'))
        await session.execute(text('DELETE FROM tags'))

        await session.commit()

        # Verify cleanup
        result = await session.execute(text('SELECT COUNT(*) FROM videos'))
        video_count = result.scalar()

        result = await session.execute(text('SELECT COUNT(*) FROM transcriptions'))
        transcription_count = result.scalar()

        result = await session.execute(text('SELECT COUNT(*) FROM tags'))
        tag_count = result.scalar()

        logger.info(f'After cleanup: {video_count} videos, {transcription_count} transcriptions, {tag_count} tags')
        logger.info('✅ Production database cleanup complete!')

if __name__ == '__main__':
    asyncio.run(cleanup_database())
