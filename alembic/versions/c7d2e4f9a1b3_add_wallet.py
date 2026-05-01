"""add wallet

Revision ID: c7d2e4f9a1b3
Revises: f8a3c9b1d2e5
Create Date: 2026-05-01 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'c7d2e4f9a1b3'
down_revision = 'f8a3c9b1d2e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'wallet',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('balance', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'wallet_transactions',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('donation', 'redemption', name='wallet_transaction_type'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('order_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_wallet_transactions_order_id', 'wallet_transactions', ['order_id'])

    op.add_column('orders', sa.Column('donation_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'))
    op.add_column('orders', sa.Column('wallet_subsidy', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'))

    # Seed the singleton wallet row.
    op.execute("INSERT INTO wallet (id, balance) VALUES (1, 0)")


def downgrade() -> None:
    op.drop_column('orders', 'wallet_subsidy')
    op.drop_column('orders', 'donation_amount')
    op.drop_index('ix_wallet_transactions_order_id', 'wallet_transactions')
    op.drop_table('wallet_transactions')
    op.drop_table('wallet')
    op.execute("DROP TYPE IF EXISTS wallet_transaction_type")
