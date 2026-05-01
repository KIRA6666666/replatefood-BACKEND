import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus


async def get_by_id(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    return await db.get(Order, order_id)


async def list_for_customer(
    db: AsyncSession,
    customer_id: uuid.UUID,
    *,
    status: OrderStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Order]:
    stmt = select(Order).where(Order.customer_id == customer_id)
    if status is not None:
        stmt = stmt.where(Order.status == status)
    stmt = stmt.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_for_restaurant(
    db: AsyncSession,
    restaurant_id: uuid.UUID,
    *,
    status: OrderStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Order]:
    stmt = select(Order).where(Order.restaurant_id == restaurant_id)
    if status is not None:
        stmt = stmt.where(Order.status == status)
    stmt = stmt.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_all(
    db: AsyncSession,
    *,
    status: OrderStatus | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Order]:
    stmt = select(Order)
    if status is not None:
        stmt = stmt.where(Order.status == status)
    stmt = stmt.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
