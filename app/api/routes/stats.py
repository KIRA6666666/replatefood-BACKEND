from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DbSession
from app.models.customer_profile import CustomerProfile
from app.models.order import Order, OrderStatus
from app.models.wallet import Wallet

router = APIRouter(prefix="/stats", tags=["stats"])


class PlatformStats(BaseModel):
    meals_rescued: int
    fund_balance: float
    students_helped: int


@router.get("", response_model=PlatformStats)
async def get_stats(db: DbSession) -> PlatformStats:
    meals_rescued = (
        await db.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.delivered)
        )
    ).scalar_one()

    wallet = await db.get(Wallet, 1)
    fund_balance = float(wallet.balance) if wallet else 0.0

    students_helped = (
        await db.execute(
            select(func.count(CustomerProfile.id)).where(
                CustomerProfile.is_student.is_(True)
            )
        )
    ).scalar_one()

    return PlatformStats(
        meals_rescued=int(meals_rescued),
        fund_balance=fund_balance,
        students_helped=int(students_helped),
    )
