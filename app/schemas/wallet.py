import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.wallet import WalletTransactionType


class WalletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    balance: Decimal


class WalletTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: WalletTransactionType
    amount: Decimal
    order_id: uuid.UUID | None
    created_at: datetime
