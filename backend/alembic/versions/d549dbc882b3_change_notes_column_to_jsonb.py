"""change notes column to jsonb

Revision ID: d549dbc882b3
Revises: 6478b532d83d
Create Date: 2025-11-12 21:05:44.749666

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd549dbc882b3'
down_revision: Union[str, Sequence[str], None] = '6478b532d83d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Convert text column to JSONB using explicit cast
    op.execute('ALTER TABLE transcriptions ALTER COLUMN notes TYPE JSONB USING notes::jsonb')


def downgrade() -> None:
    """Downgrade schema."""
    # Convert JSONB column back to text
    op.execute('ALTER TABLE transcriptions ALTER COLUMN notes TYPE TEXT')
