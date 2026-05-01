import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession, require_role
from app.core.config import settings
from app.crud import customer_profile as customer_crud
from app.crud import offer as offer_crud
from app.crud import order as order_crud
from app.crud import restaurant_profile as restaurant_crud
from app.models.order import Order, OrderStatus
from app.models.user import UserRole
from app.schemas.order import OrderCreate, OrderRead, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


_RESTAURANT_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.pending: {OrderStatus.confirmed, OrderStatus.cancelled},
    OrderStatus.confirmed: {OrderStatus.preparing, OrderStatus.cancelled},
    OrderStatus.preparing: {OrderStatus.out_for_delivery, OrderStatus.cancelled},
    OrderStatus.out_for_delivery: {OrderStatus.delivered, OrderStatus.cancelled},
    OrderStatus.delivered: set(),
    OrderStatus.cancelled: set(),
}


@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.customer))],
)
async def place_order(
    payload: OrderCreate, db: DbSession, current_user: CurrentUser
) -> OrderRead:
    customer = await customer_crud.get_by_user_id(db, current_user.id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create a customer profile before placing orders",
        )
    offer = await offer_crud.get_by_id(db, payload.offer_id)
    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found"
        )
    if not offer.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Offer is not active"
        )
    if offer.expiry_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Offer has expired"
        )
    if offer.quantity_available < payload.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough portions available",
        )

    delivery_fee: Decimal = settings.DEFAULT_DELIVERY_FEE
    total_price = (offer.discounted_price * payload.quantity) + delivery_fee

    offer.quantity_available -= payload.quantity
    if offer.quantity_available == 0:
        offer.is_active = False

    order = Order(
        customer_id=customer.id,
        restaurant_id=offer.restaurant_id,
        offer_id=offer.id,
        quantity=payload.quantity,
        total_price=total_price,
        delivery_fee=delivery_fee,
        delivery_address=payload.delivery_address,
        delivery_lat=payload.delivery_lat,
        delivery_lng=payload.delivery_lng,
        status=OrderStatus.pending,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return OrderRead.model_validate(order)


@router.get(
    "/me",
    response_model=list[OrderRead],
    dependencies=[Depends(require_role(UserRole.customer))],
)
async def list_my_orders(
    db: DbSession,
    current_user: CurrentUser,
    order_status: Annotated[OrderStatus | None, Query(alias="status")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[OrderRead]:
    customer = await customer_crud.get_by_user_id(db, current_user.id)
    if customer is None:
        return []
    orders = await order_crud.list_for_customer(
        db, customer.id, status=order_status, skip=skip, limit=limit
    )
    return [OrderRead.model_validate(o) for o in orders]


@router.get(
    "/restaurant",
    response_model=list[OrderRead],
    dependencies=[Depends(require_role(UserRole.restaurant))],
)
async def list_restaurant_orders(
    db: DbSession,
    current_user: CurrentUser,
    order_status: Annotated[OrderStatus | None, Query(alias="status")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[OrderRead]:
    profile = await restaurant_crud.get_by_user_id(db, current_user.id)
    if profile is None:
        return []
    orders = await order_crud.list_for_restaurant(
        db, profile.id, status=order_status, skip=skip, limit=limit
    )
    return [OrderRead.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> OrderRead:
    order = await order_crud.get_by_id(db, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    if current_user.role == UserRole.admin:
        return OrderRead.model_validate(order)
    if current_user.role == UserRole.customer:
        customer = await customer_crud.get_by_user_id(db, current_user.id)
        if customer is None or order.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
            )
        return OrderRead.model_validate(order)
    if current_user.role == UserRole.restaurant:
        profile = await restaurant_crud.get_by_user_id(db, current_user.id)
        if profile is None or order.restaurant_id != profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
            )
        return OrderRead.model_validate(order)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    dependencies=[Depends(require_role(UserRole.restaurant))],
)
async def update_order_status(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> OrderRead:
    order = await order_crud.get_by_id(db, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    profile = await restaurant_crud.get_by_user_id(db, current_user.id)
    if profile is None or order.restaurant_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify orders for another restaurant",
        )
    allowed = _RESTAURANT_TRANSITIONS.get(order.status, set())
    if payload.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition order from {order.status.value} to {payload.status.value}",
        )
    order.status = payload.status
    if payload.estimated_delivery_time is not None:
        order.estimated_delivery_time = payload.estimated_delivery_time
    await db.commit()
    await db.refresh(order)
    return OrderRead.model_validate(order)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderRead,
    dependencies=[Depends(require_role(UserRole.customer))],
)
async def cancel_my_order(
    order_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> OrderRead:
    order = await order_crud.get_by_id(db, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    customer = await customer_crud.get_by_user_id(db, current_user.id)
    if customer is None or order.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    if order.status in {OrderStatus.delivered, OrderStatus.cancelled}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in status {order.status.value}",
        )
    if order.status not in {OrderStatus.pending, OrderStatus.confirmed}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order can no longer be cancelled by the customer",
        )
    order.status = OrderStatus.cancelled
    offer = await offer_crud.get_by_id(db, order.offer_id)
    if offer is not None:
        offer.quantity_available += order.quantity
        if offer.quantity_available > 0 and offer.expiry_time > datetime.now(timezone.utc):
            offer.is_active = True
    await db.commit()
    await db.refresh(order)
    return OrderRead.model_validate(order)
