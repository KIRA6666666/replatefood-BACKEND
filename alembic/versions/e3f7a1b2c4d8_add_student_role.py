"""add student role to user_role enum

Revision ID: e3f7a1b2c4d8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-09 00:00:00.000000
"""
from alembic import op

revision = 'e3f7a1b2c4d8'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'student'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; a full type recreation is required.
    # Downgrade is intentionally left as a no-op — remove manually if needed.
    pass
