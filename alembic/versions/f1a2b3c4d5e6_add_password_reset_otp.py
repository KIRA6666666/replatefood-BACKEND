"""add password_reset_otps table

Revision ID: f1a2b3c4d5e6
Revises: e3f7a1b2c4d8
Create Date: 2026-05-09 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = 'f1a2b3c4d5e6'
down_revision = 'e3f7a1b2c4d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'password_reset_otps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('password_reset_otps')
