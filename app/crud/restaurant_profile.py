import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant_profile import RestaurantProfile, RestaurantStatus
from app.schemas.restaurant_profile import RestaurantProfileCreate, RestaurantProfileUpdate


async def get_by_id(db: AsyncSession, profile_id: uuid.UUID) -> RestaurantProfile | None:
    return await db.get(RestaurantProfile, profile_id)


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> RestaurantProfile | None:
    result = await db.execute(
        select(RestaurantProfile).where(RestaurantProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_all(
    db: AsyncSession,
    *,
    status: RestaurantStatus | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[RestaurantProfile]:
    stmt = select(RestaurantProfile)
    if status is not None:
        stmt = stmt.where(RestaurantProfile.status == status)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create(
    db: AsyncSession, user_id: uuid.UUID, payload: RestaurantProfileCreate
) -> RestaurantProfile:
    profile = RestaurantProfile(user_id=user_id, **payload.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update(
    db: AsyncSession, profile: RestaurantProfile, payload: RestaurantProfileUpdate
) -> RestaurantProfile:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile


async def set_status(
    db: AsyncSession, profile: RestaurantProfile, status: RestaurantStatus
) -> RestaurantProfile:
    profile.status = status
    await db.commit()
    await db.refresh(profile)
    return profile
