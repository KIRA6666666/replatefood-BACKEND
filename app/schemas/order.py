import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    offer_id: uuid.UUID
    quantity: int = Field(ge=1)
    delivery_address: str = Field(min_length=1, max_length=255)
    delivery_lat: float | None = Field(default=None, ge=-90, le=90)
    delivery_lng: float | None = Field(default=None, ge=-180, le=180)
    donation_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    restaurant_id: uuid.UUID
    offer_id: uuid.UUID
    quantity: int
    total_price: Decimal
    delivery_fee: Decimal
    delivery_address: str
    delivery_lat: float | None
    delivery_lng: float | None
    estimated_delivery_time: datetime | None
    donation_amount: Decimal
    wallet_subsidy: Decimal
    status: OrderStatus
    created_at: datetime


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    estimated_delivery_time: datetime | None = None
