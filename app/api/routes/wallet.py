from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, require_role
from app.crud import wallet as wallet_crud
from app.models.user import UserRole
from app.schemas.wallet import WalletRead, WalletTransactionRead

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/balance", response_model=WalletRead)
async def get_balance(db: DbSession) -> WalletRead:
    wallet = await wallet_crud.get_wallet(db)
    return WalletRead.model_validate(wallet)


@router.get(
    "/transactions",
    response_model=list[WalletTransactionRead],
    dependencies=[Depends(require_role(UserRole.admin))],
)
async def list_transactions(
    db: DbSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[WalletTransactionRead]:
    txs = await wallet_crud.list_transactions(db, skip=skip, limit=limit)
    return [WalletTransactionRead.model_validate(t) for t in txs]
