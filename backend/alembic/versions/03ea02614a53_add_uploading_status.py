"""add_uploading_status

Revision ID: 03ea02614a53
Revises: a9412bb22018
Create Date: 2025-11-20 10:53:01.256339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03ea02614a53'
down_revision: Union[str, Sequence[str], None] = 'a9412bb22018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add 'uploading' to the VideoStatus enum
    op.execute("ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'uploading'")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave the value in the enum (it won't cause issues)
    pass
