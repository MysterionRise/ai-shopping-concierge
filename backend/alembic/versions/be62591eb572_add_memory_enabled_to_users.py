"""add memory_enabled to users

Revision ID: be62591eb572
Revises: c4c1eec2659c
Create Date: 2026-02-18 20:09:14.508932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be62591eb572'
down_revision: Union[str, None] = 'c4c1eec2659c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('memory_enabled', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'memory_enabled')
