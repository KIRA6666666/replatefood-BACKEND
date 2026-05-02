"""add cuisine_type, meal_category, pickup_time_minutes to offers

Revision ID: a1b2c3d4e5f6
Revises: c7d2e4f9a1b3
Create Date: 2026-05-02 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'c7d2e4f9a1b3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('offers', sa.Column('cuisine_type', sa.String(50), nullable=True))
    op.add_column('offers', sa.Column('meal_category', sa.String(50), nullable=True))
    op.add_column('offers', sa.Column('pickup_time_minutes', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('offers', 'pickup_time_minutes')
    op.drop_column('offers', 'meal_category')
    op.drop_column('offers', 'cuisine_type')
