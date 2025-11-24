#!/usr/bin/env python3
"""
Database Reset Script

Clears all data from database tables and resets sequences/indexes.
Preserves table structure and schema.

Usage:
    uv run python scripts/reset_database.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine, Base
from app.models import Video, Transcription


async def reset_database():
    """Clear all data and reset sequences"""
    async with engine.begin() as conn:
        print("🗑️  Clearing database tables...")

        # Disable foreign key constraints temporarily
        await conn.execute(text("SET session_replication_role = 'replica';"))

        # Truncate all tables and reset sequences
        print("  → Truncating transcriptions table...")
        await conn.execute(text("TRUNCATE TABLE transcriptions RESTART IDENTITY CASCADE;"))

        print("  → Truncating videos table...")
        await conn.execute(text("TRUNCATE TABLE videos RESTART IDENTITY CASCADE;"))

        # Re-enable foreign key constraints
        await conn.execute(text("SET session_replication_role = 'origin';"))

        # Reset sequences (in case RESTART IDENTITY didn't work)
        print("  → Resetting sequences...")
        await conn.execute(text("SELECT setval(pg_get_serial_sequence('videos', 'id'), 1, false);"))
        await conn.execute(text("SELECT setval(pg_get_serial_sequence('transcriptions', 'id'), 1, false);"))

        print("✅ Database reset complete")
        print("  → All data cleared")
        print("  → Sequences reset to 1")


async def verify_reset():
    """Verify tables are empty"""
    async with engine.connect() as conn:
        videos_count = await conn.execute(text("SELECT COUNT(*) FROM videos;"))
        transcriptions_count = await conn.execute(text("SELECT COUNT(*) FROM transcriptions;"))

        videos = videos_count.scalar()
        transcriptions = transcriptions_count.scalar()

        print("\n📊 Verification:")
        print(f"  → Videos: {videos} rows")
        print(f"  → Transcriptions: {transcriptions} rows")

        if videos == 0 and transcriptions == 0:
            print("✅ All tables empty")
        else:
            print("⚠️  Tables not empty - reset may have failed")


async def main():
    """Main execution"""
    print("=" * 50)
    print("Database Reset Script")
    print("=" * 50)

    try:
        await reset_database()
        await verify_reset()
        print("\n✅ Success - database reset complete")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
