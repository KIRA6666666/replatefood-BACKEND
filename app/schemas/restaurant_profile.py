import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.restaurant_profile import RestaurantStatus


class RestaurantProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=255)
    delivery_radius_km: float = Field(ge=0, le=100, default=5.0)
    logo_url: str | None = Field(default=None, max_length=512)
    photos: list[str] = Field(default_factory=list)
    description: str | None = None


class RestaurantProfileCreate(RestaurantProfileBase):
    pass


class RestaurantProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    delivery_radius_km: float | None = Field(default=None, ge=0, le=100)
    logo_url: str | None = Field(default=None, max_length=512)
    photos: list[str] | None = None
    description: str | None = None


class RestaurantProfileRead(RestaurantProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    status: RestaurantStatus


class RestaurantStatusUpdate(BaseModel):
    status: RestaurantStatus
