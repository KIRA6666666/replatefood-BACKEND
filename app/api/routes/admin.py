import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DbSession, require_role
from app.crud import order as order_crud
from app.crud import restaurant_profile as restaurant_crud
from app.models.offer import Offer
from app.models.order import Order, OrderStatus
from app.models.restaurant_profile import RestaurantProfile, RestaurantStatus
from app.models.user import User, UserRole
from app.schemas.order import OrderRead
from app.schemas.restaurant_profile import (
    RestaurantProfileRead,
    RestaurantStatusUpdate,
)
from app.schemas.user import UserRead

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(UserRole.admin))],
)


class PlatformAnalytics(BaseModel):
    total_users: int
    total_customers: int
    total_restaurants: int
    pending_restaurants: int
    approved_restaurants: int
    suspended_restaurants: int
    total_offers: int
    active_offers: int
    total_orders: int
    orders_by_status: dict[str, int]


@router.get("/users", response_model=list[UserRead])
async def list_users(
    db: DbSession,
    role: UserRole | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[UserRead]:
    stmt = select(User)
    if role is not None:
        stmt = stmt.where(User.role == role)
    stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return [UserRead.model_validate(u) for u in result.scalars().all()]


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, db: DbSession) -> None:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    await db.delete(user)
    await db.commit()


@router.get("/restaurants", response_model=list[RestaurantProfileRead])
async def list_restaurants(
    db: DbSession,
    restaurant_status: Annotated[RestaurantStatus | None, Query(alias="status")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[RestaurantProfileRead]:
    profiles = await restaurant_crud.list_all(
        db, status=restaurant_status, skip=skip, limit=limit
    )
    return [RestaurantProfileRead.model_validate(p) for p in profiles]


@router.patch("/restaurants/{restaurant_id}/status", response_model=RestaurantProfileRead)
async def set_restaurant_status(
    restaurant_id: uuid.UUID, payload: RestaurantStatusUpdate, db: DbSession
) -> RestaurantProfileRead:
    profile = await restaurant_crud.get_by_id(db, restaurant_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found"
        )
    profile = await restaurant_crud.set_status(db, profile, payload.status)
    return RestaurantProfileRead.model_validate(profile)


@router.get("/orders", response_model=list[OrderRead])
async def list_orders(
    db: DbSession,
    order_status: Annotated[OrderStatus | None, Query(alias="status")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[OrderRead]:
    orders = await order_crud.list_all(
        db, status=order_status, skip=skip, limit=limit
    )
    return [OrderRead.model_validate(o) for o in orders]


@router.get("/analytics", response_model=PlatformAnalytics)
async def get_analytics(db: DbSession) -> PlatformAnalytics:
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_customers = (
        await db.execute(
            select(func.count(User.id)).where(User.role == UserRole.customer)
        )
    ).scalar_one()
    total_restaurants = (
        await db.execute(select(func.count(RestaurantProfile.id)))
    ).scalar_one()
    pending_restaurants = (
        await db.execute(
            select(func.count(RestaurantProfile.id)).where(
                RestaurantProfile.status == RestaurantStatus.pending
            )
        )
    ).scalar_one()
    approved_restaurants = (
        await db.execute(
            select(func.count(RestaurantProfile.id)).where(
                RestaurantProfile.status == RestaurantStatus.approved
            )
        )
    ).scalar_one()
    suspended_restaurants = (
        await db.execute(
            select(func.count(RestaurantProfile.id)).where(
                RestaurantProfile.status == RestaurantStatus.suspended
            )
        )
    ).scalar_one()
    total_offers = (await db.execute(select(func.count(Offer.id)))).scalar_one()
    active_offers = (
        await db.execute(
            select(func.count(Offer.id)).where(Offer.is_active.is_(True))
        )
    ).scalar_one()
    total_orders = (await db.execute(select(func.count(Order.id)))).scalar_one()

    by_status_rows = await db.execute(
        select(Order.status, func.count(Order.id)).group_by(Order.status)
    )
    orders_by_status = {s.value: int(c) for s, c in by_status_rows.all()}

    return PlatformAnalytics(
        total_users=int(total_users),
        total_customers=int(total_customers),
        total_restaurants=int(total_restaurants),
        pending_restaurants=int(pending_restaurants),
        approved_restaurants=int(approved_restaurants),
        suspended_restaurants=int(suspended_restaurants),
        total_offers=int(total_offers),
        active_offers=int(active_offers),
        total_orders=int(total_orders),
        orders_by_status=orders_by_status,
    )
