import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OfferBase(BaseModel):
    meal_name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    photos: list[str] = Field(default_factory=list)
    original_price: Decimal = Field(ge=0, decimal_places=2)
    discounted_price: Decimal = Field(ge=0, decimal_places=2)
    student_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    quantity_available: int = Field(ge=0)
    expiry_time: datetime
    is_active: bool = True
    delivery_available: bool = False
    inplace_available: bool = True
    cuisine_type: str | None = Field(default=None, max_length=50)
    meal_category: str | None = Field(default=None, max_length=50)
    pickup_time_minutes: int | None = Field(default=None, ge=1)


class OfferCreate(OfferBase):
    pass


class OfferUpdate(BaseModel):
    meal_name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    photos: list[str] | None = None
    original_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    discounted_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    student_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    quantity_available: int | None = Field(default=None, ge=0)
    expiry_time: datetime | None = None
    is_active: bool | None = None
    delivery_available: bool | None = None
    inplace_available: bool | None = None
    cuisine_type: str | None = Field(default=None, max_length=50)
    meal_category: str | None = Field(default=None, max_length=50)
    pickup_time_minutes: int | None = Field(default=None, ge=1)


class OfferRead(OfferBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurant_id: uuid.UUID
    created_at: datetime
