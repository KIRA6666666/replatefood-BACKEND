from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, DbSession, require_role
from app.crud import customer_profile as customer_crud
from app.models.user import UserRole
from app.schemas.customer_profile import (
    CustomerProfileCreate,
    CustomerProfileRead,
    CustomerProfileUpdate,
)

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    dependencies=[Depends(require_role(UserRole.customer))],
)


@router.post("/me", response_model=CustomerProfileRead, status_code=status.HTTP_201_CREATED)
async def create_my_profile(
    payload: CustomerProfileCreate, db: DbSession, current_user: CurrentUser
) -> CustomerProfileRead:
    if await customer_crud.get_by_user_id(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer profile already exists",
        )
    profile = await customer_crud.create(db, current_user.id, payload)
    return CustomerProfileRead.model_validate(profile)


@router.get("/me", response_model=CustomerProfileRead)
async def read_my_profile(
    db: DbSession, current_user: CurrentUser
) -> CustomerProfileRead:
    profile = await customer_crud.get_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found"
        )
    return CustomerProfileRead.model_validate(profile)


@router.patch("/me", response_model=CustomerProfileRead)
async def update_my_profile(
    payload: CustomerProfileUpdate, db: DbSession, current_user: CurrentUser
) -> CustomerProfileRead:
    profile = await customer_crud.get_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found"
        )
    profile = await customer_crud.update(db, profile, payload)
    return CustomerProfileRead.model_validate(profile)
