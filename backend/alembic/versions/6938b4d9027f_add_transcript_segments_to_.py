"""add_transcript_segments_to_transcriptions

Revision ID: 6938b4d9027f
Revises: 81743a8eb5f6
Create Date: 2025-11-16 14:54:02.040701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '6938b4d9027f'
down_revision: Union[str, Sequence[str], None] = '81743a8eb5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add transcript_segments JSONB column to transcriptions table."""
    op.add_column(
        'transcriptions',
        sa.Column('transcript_segments', JSONB, nullable=True)
    )


def downgrade() -> None:
    """Remove transcript_segments column from transcriptions table."""
    op.drop_column('transcriptions', 'transcript_segments')
