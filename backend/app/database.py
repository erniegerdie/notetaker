from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings
import os

# Convert postgresql:// to postgresql+asyncpg://
database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

# Cloud SQL connection configuration
# When running on Cloud Run, use Unix socket connection
# Connection string format: postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
if os.getenv("K_SERVICE"):  # K_SERVICE env var indicates Cloud Run environment
    # Extract components from DATABASE_URL if it's in standard format
    # and convert to Unix socket format for Cloud SQL
    if "/cloudsql/" not in database_url:
        # Running on Cloud Run but DATABASE_URL not configured for Unix socket
        # This should be configured via Secret Manager
        pass

engine_args = {
    "echo": False,
    "future": True,
    "pool_size": 20,  # Increase pool size for concurrent operations
    "max_overflow": 40,  # Allow more overflow connections
    "pool_timeout": 30,  # Wait up to 30s for a connection
    "pool_recycle": 3600,  # Recycle connections after 1 hour
    "pool_pre_ping": True,  # Verify connections before using them
    "pool_pre_ping": True,  # Test connections before checkout
}

# Adjust pool settings for Cloud Run (more conservative)
if os.getenv("K_SERVICE"):
    engine_args["pool_size"] = 5
    engine_args["max_overflow"] = 10

# Create engine with pool_pre_ping to avoid startup connection requirement
engine = create_async_engine(database_url, **engine_args)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
