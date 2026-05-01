import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

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
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    default_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    default_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_student: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    user = relationship("User", back_populates="customer_profile")
    orders = relationship(
        "Order", back_populates="customer", cascade="all, delete-orphan"
    )
