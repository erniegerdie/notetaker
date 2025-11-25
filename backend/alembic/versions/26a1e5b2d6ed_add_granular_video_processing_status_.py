"""Add granular video processing status states

Revision ID: 26a1e5b2d6ed
Revises: 4cdcc640fbd5
Create Date: 2025-11-25 06:22:41.076390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26a1e5b2d6ed'
down_revision: Union[str, Sequence[str], None] = '4cdcc640fbd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add granular processing status states."""
    # Add new enum values to videostatus enum type
    op.execute("ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'downloading'")
    op.execute("ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'extracting_audio'")
    op.execute("ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'transcribing'")
    op.execute("ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'generating_notes'")


def downgrade() -> None:
    """Downgrade schema - enum values cannot be removed in PostgreSQL."""
    # Note: PostgreSQL does not support removing enum values directly
    # Downgrade would require recreating the enum type and migrating data
    # For now, we leave the new values in place (they won't cause issues)
    pass
