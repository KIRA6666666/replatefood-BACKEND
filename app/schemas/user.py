import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.customer


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: UserRole
    created_at: datetime


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
