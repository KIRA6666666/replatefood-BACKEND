import enum
import uuid

from sqlalchemy import Enum as SQLEnum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RestaurantStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    suspended = "suspended"


class RestaurantProfile(Base):
    __tablename__ = "restaurant_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    delivery_radius_km: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    photos: Mapped[list[str]] = mapped_column(
        ARRAY(String(512)), nullable=False, default=list, server_default="{}"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RestaurantStatus] = mapped_column(
        SQLEnum(RestaurantStatus, name="restaurant_status"),
        nullable=False,
        default=RestaurantStatus.pending,
        server_default=RestaurantStatus.pending.value,
    )

    user = relationship("User", back_populates="restaurant_profile")
    offers = relationship(
        "Offer", back_populates="restaurant", cascade="all, delete-orphan"
    )
    orders = relationship("Order", back_populates="restaurant")
