"""add student features

Revision ID: f8a3c9b1d2e5
Revises: dba240aa8221
Create Date: 2026-05-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'f8a3c9b1d2e5'
down_revision = 'dba240aa8221'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('customer_profiles',
        sa.Column('is_student', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('offers',
        sa.Column('student_price', sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('customer_profiles', 'is_student')
    op.drop_column('offers', 'student_price')
