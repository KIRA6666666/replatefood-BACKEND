import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DbSession, require_role
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

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(UserRole.admin))],
)


class PaginatedUsers(BaseModel):
    items: list[UserRead]
    total: int


class PaginatedRestaurants(BaseModel):
    items: list[RestaurantProfileRead]
    total: int


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


@router.get("/users", response_model=PaginatedUsers)
async def list_users(
    db: DbSession,
    role: UserRole | None = None,
    search: str | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 15,
) -> PaginatedUsers:
    stmt = select(User)
    if role is not None:
        stmt = stmt.where(User.role == role)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(User.username.ilike(pattern), User.email.ilike(pattern)))
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    result = await db.execute(stmt.order_by(User.created_at.desc()).offset(skip).limit(limit))
    return PaginatedUsers(
        items=[UserRead.model_validate(u) for u in result.scalars().all()],
        total=int(total),
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> None:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    await db.delete(user)
    await db.commit()
    logger.info(
        "admin deleted user",
        extra={
            "actor_id": str(current_user.id),
            "target_user_id": str(user_id),
            "target_email": user.email,
            "target_role": user.role.value,
        },
    )


@router.get("/restaurants", response_model=PaginatedRestaurants)
async def list_restaurants(
    db: DbSession,
    restaurant_status: Annotated[RestaurantStatus | None, Query(alias="status")] = None,
    search: str | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 15,
) -> PaginatedRestaurants:
    stmt = select(RestaurantProfile)
    if restaurant_status is not None:
        stmt = stmt.where(RestaurantProfile.status == restaurant_status)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(RestaurantProfile.name.ilike(pattern), RestaurantProfile.location.ilike(pattern))
        )
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    result = await db.execute(stmt.order_by(RestaurantProfile.name).offset(skip).limit(limit))
    return PaginatedRestaurants(
        items=[RestaurantProfileRead.model_validate(p) for p in result.scalars().all()],
        total=int(total),
    )


@router.patch("/restaurants/{restaurant_id}/status", response_model=RestaurantProfileRead)
async def set_restaurant_status(
    restaurant_id: uuid.UUID,
    payload: RestaurantStatusUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> RestaurantProfileRead:
    profile = await restaurant_crud.get_by_id(db, restaurant_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found"
        )
    old_status = profile.status
    profile = await restaurant_crud.set_status(db, profile, payload.status)
    logger.info(
        "admin changed restaurant status",
        extra={
            "actor_id": str(current_user.id),
            "restaurant_id": str(restaurant_id),
            "old_status": old_status.value,
            "new_status": profile.status.value,
        },
    )
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
