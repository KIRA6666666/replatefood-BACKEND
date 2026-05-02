"""add delivery_available and inplace_available to offers

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-02 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('offers', sa.Column('delivery_available', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('offers', sa.Column('inplace_available', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('offers', 'inplace_available')
    op.drop_column('offers', 'delivery_available')
