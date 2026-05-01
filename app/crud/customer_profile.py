import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer_profile import CustomerProfile
from app.schemas.customer_profile import CustomerProfileCreate, CustomerProfileUpdate


async def get_by_id(db: AsyncSession, profile_id: uuid.UUID) -> CustomerProfile | None:
    return await db.get(CustomerProfile, profile_id)


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> CustomerProfile | None:
    result = await db.execute(
        select(CustomerProfile).where(CustomerProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession, user_id: uuid.UUID, payload: CustomerProfileCreate
) -> CustomerProfile:
    profile = CustomerProfile(user_id=user_id, **payload.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update(
    db: AsyncSession, profile: CustomerProfile, payload: CustomerProfileUpdate
) -> CustomerProfile:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile
