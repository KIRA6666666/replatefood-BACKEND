"""add offer_templates table

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-05-09 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, UUID

revision = 'b3c4d5e6f7a8'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'offer_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('restaurant_id', UUID(as_uuid=True), sa.ForeignKey('restaurant_profiles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('meal_name', sa.String(150), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('cuisine_type', sa.String(50), nullable=True),
        sa.Column('meal_category', sa.String(50), nullable=True),
        sa.Column('pickup_time_minutes', sa.Integer, nullable=True),
        sa.Column('photos', ARRAY(sa.String(512)), nullable=False, server_default='{}'),
        sa.Column('original_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('discounted_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('student_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('delivery_available', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('inplace_available', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('offer_templates')
