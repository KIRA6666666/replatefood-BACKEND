import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet, WalletTransaction, WalletTransactionType


async def get_wallet(db: AsyncSession) -> Wallet:
    wallet = await db.get(Wallet, 1)
    if wallet is None:
        wallet = Wallet(id=1, balance=Decimal("0.00"))
        db.add(wallet)
        await db.flush()
    return wallet


async def add_donation(
    db: AsyncSession, amount: Decimal, order_id: uuid.UUID
) -> WalletTransaction:
    wallet = await get_wallet(db)
    wallet.balance += amount
    tx = WalletTransaction(
        type=WalletTransactionType.donation,
        amount=amount,
        order_id=order_id,
    )
    db.add(tx)
    return tx


async def redeem_subsidy(
    db: AsyncSession, amount: Decimal, order_id: uuid.UUID
) -> Decimal:
    """Deduct up to `amount` from the wallet. Returns the amount actually redeemed."""
    wallet = await get_wallet(db)
    redeemed = min(amount, wallet.balance)
    if redeemed <= 0:
        return Decimal("0.00")
    wallet.balance -= redeemed
    tx = WalletTransaction(
        type=WalletTransactionType.redemption,
        amount=redeemed,
        order_id=order_id,
    )
    db.add(tx)
    return redeemed


async def list_transactions(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[WalletTransaction]:
    result = await db.execute(
        select(WalletTransaction)
        .order_by(WalletTransaction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
