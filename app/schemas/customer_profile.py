import uuid

from pydantic import BaseModel, ConfigDict, Field


class CustomerProfileBase(BaseModel):
    phone_number: str | None = Field(default=None, max_length=32)
    default_address: str | None = Field(default=None, max_length=255)
    default_lat: float | None = Field(default=None, ge=-90, le=90)
    default_lng: float | None = Field(default=None, ge=-180, le=180)
    is_student: bool = False


class CustomerProfileCreate(CustomerProfileBase):
    pass


class CustomerProfileUpdate(CustomerProfileBase):
    pass


class CustomerProfileRead(CustomerProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
