import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.offer import Offer
from app.schemas.offer import OfferCreate, OfferUpdate


async def get_by_id(db: AsyncSession, offer_id: uuid.UUID) -> Offer | None:
    return await db.get(Offer, offer_id)


async def list_offers(
    db: AsyncSession,
    *,
    restaurant_id: uuid.UUID | None = None,
    only_active: bool = False,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    location: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Offer]:
    from app.models.restaurant_profile import RestaurantProfile

    stmt = select(Offer)
    if restaurant_id is not None:
        stmt = stmt.where(Offer.restaurant_id == restaurant_id)
    if only_active:
        now = datetime.now(timezone.utc)
        stmt = stmt.where(
            Offer.is_active.is_(True),
            Offer.expiry_time > now,
            Offer.quantity_available > 0,
        )
    if min_price is not None:
        stmt = stmt.where(Offer.discounted_price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Offer.discounted_price <= max_price)
    if location:
        stmt = stmt.join(RestaurantProfile, RestaurantProfile.id == Offer.restaurant_id).where(
            RestaurantProfile.location.ilike(f"%{location}%")
        )
    stmt = stmt.order_by(Offer.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create(
    db: AsyncSession, restaurant_id: uuid.UUID, payload: OfferCreate
) -> Offer:
    offer = Offer(restaurant_id=restaurant_id, **payload.model_dump())
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return offer


async def update(db: AsyncSession, offer: Offer, payload: OfferUpdate) -> Offer:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(offer, field, value)
    await db.commit()
    await db.refresh(offer)
    return offer


async def delete(db: AsyncSession, offer: Offer) -> None:
    await db.delete(offer)
    await db.commit()
