"""add user_id columns for authentication

Revision ID: a1b2c3d4e5f6
Revises: fe2fbd5c0651
Create Date: 2025-11-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fe2fbd5c0651'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id column to videos table
    op.add_column('videos', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_videos_user_id', 'videos', ['user_id'], unique=False)

    # Add user_id column to collections table
    op.add_column('collections', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_collections_user_id', 'collections', ['user_id'], unique=False)

    # Add user_id column to tags table
    op.add_column('tags', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_tags_user_id', 'tags', ['user_id'], unique=False)


def downgrade() -> None:
    # Remove user_id columns and indexes
    op.drop_index('ix_tags_user_id', table_name='tags')
    op.drop_column('tags', 'user_id')

    op.drop_index('ix_collections_user_id', table_name='collections')
    op.drop_column('collections', 'user_id')

    op.drop_index('ix_videos_user_id', table_name='videos')
    op.drop_column('videos', 'user_id')
