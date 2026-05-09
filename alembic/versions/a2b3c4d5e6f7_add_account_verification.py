"""add account verification otp and is_verified to users

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-05-09 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = 'a2b3c4d5e6f7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    col_exists = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name='users' AND column_name='is_verified'"
    )).scalar()
    if not col_exists:
        op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))

    table_exists = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_name='account_verification_otps'"
    )).scalar()
    if table_exists:
        return

    op.create_table(
        'account_verification_otps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('account_verification_otps')
    op.drop_column('users', 'is_verified')
