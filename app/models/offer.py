import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurant_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meal_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cuisine_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    meal_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pickup_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    photos: Mapped[list[str]] = mapped_column(
        ARRAY(String(512)), nullable=False, default=list, server_default="{}"
    )
    original_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discounted_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    student_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expiry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivery_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    inplace_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    restaurant = relationship("RestaurantProfile", back_populates="offers")
    orders = relationship("Order", back_populates="offer")
