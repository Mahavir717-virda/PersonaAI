"""Add failed_ids to sync_histories

Revision ID: abfaf894e17c
Revises: 7aaffaf15651
Create Date: 2026-06-30 15:40:57.239850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'abfaf894e17c'
down_revision: Union[str, Sequence[str], None] = '7aaffaf15651'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('sync_histories', sa.Column('failed_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sync_histories', 'failed_ids')
