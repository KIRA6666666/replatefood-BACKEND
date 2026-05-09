from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DbSession
from app.models.offer import Offer
from app.models.restaurant_profile import RestaurantProfile, RestaurantStatus
from app.models.user import User

router = APIRouter(prefix="/stats", tags=["stats"])


class PlatformStats(BaseModel):
    total_users: int
    total_restaurants: int
    total_offers: int


@router.get("", response_model=PlatformStats)
async def get_stats(db: DbSession) -> PlatformStats:
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()

    total_restaurants = (
        await db.execute(
            select(func.count(RestaurantProfile.id)).where(
                RestaurantProfile.status == RestaurantStatus.approved
            )
        )
    ).scalar_one()

    total_offers = (await db.execute(select(func.count(Offer.id)))).scalar_one()

    return PlatformStats(
        total_users=int(total_users),
        total_restaurants=int(total_restaurants),
        total_offers=int(total_offers),
    )
