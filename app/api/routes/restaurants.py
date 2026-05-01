import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession, require_role
from app.crud import restaurant_profile as restaurant_crud
from app.models.restaurant_profile import RestaurantStatus
from app.models.user import UserRole
from app.schemas.restaurant_profile import (
    RestaurantProfileCreate,
    RestaurantProfileRead,
    RestaurantProfileUpdate,
)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.post(
    "/me",
    response_model=RestaurantProfileRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.restaurant))],
)
async def create_my_profile(
    payload: RestaurantProfileCreate, db: DbSession, current_user: CurrentUser
) -> RestaurantProfileRead:
    if await restaurant_crud.get_by_user_id(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Restaurant profile already exists",
        )
    profile = await restaurant_crud.create(db, current_user.id, payload)
    return RestaurantProfileRead.model_validate(profile)


@router.get(
    "/me",
    response_model=RestaurantProfileRead,
    dependencies=[Depends(require_role(UserRole.restaurant))],
)
async def read_my_profile(
    db: DbSession, current_user: CurrentUser
) -> RestaurantProfileRead:
    profile = await restaurant_crud.get_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant profile not found"
        )
    return RestaurantProfileRead.model_validate(profile)


@router.patch(
    "/me",
    response_model=RestaurantProfileRead,
    dependencies=[Depends(require_role(UserRole.restaurant))],
)
async def update_my_profile(
    payload: RestaurantProfileUpdate, db: DbSession, current_user: CurrentUser
) -> RestaurantProfileRead:
    profile = await restaurant_crud.get_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant profile not found"
        )
    profile = await restaurant_crud.update(db, profile, payload)
    return RestaurantProfileRead.model_validate(profile)


@router.get("", response_model=list[RestaurantProfileRead])
async def list_restaurants(
    db: DbSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[RestaurantProfileRead]:
    profiles = await restaurant_crud.list_all(
        db, status=RestaurantStatus.approved, skip=skip, limit=limit
    )
    return [RestaurantProfileRead.model_validate(p) for p in profiles]


@router.get("/{restaurant_id}", response_model=RestaurantProfileRead)
async def get_restaurant(
    restaurant_id: uuid.UUID, db: DbSession
) -> RestaurantProfileRead:
    profile = await restaurant_crud.get_by_id(db, restaurant_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found"
        )
    return RestaurantProfileRead.model_validate(profile)
