"""add data_completeness to products

Revision ID: c4c1eec2659c
Revises: 8a7355a4887c
Create Date: 2026-02-18 16:09:34.065749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4c1eec2659c'
down_revision: Union[str, None] = '8a7355a4887c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('data_completeness', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'data_completeness')
