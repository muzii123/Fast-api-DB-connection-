"""add password_hash to users

Revision ID: b1c2d3e4f5a6
Revises: efd026fc4a94
Create Date: 2026-06-12 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'efd026fc4a94'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add password_hash column — nullable so existing users are not broken
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_hash')
