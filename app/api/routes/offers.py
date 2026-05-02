import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession, require_role
from app.crud import offer as offer_crud
from app.crud import restaurant_profile as restaurant_crud
from app.models.restaurant_profile import RestaurantStatus
from app.models.user import UserRole
from app.schemas.offer import OfferCreate, OfferRead, OfferUpdate

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get("", response_model=list[OfferRead])
async def list_offers(
    db: DbSession,
    restaurant_id: uuid.UUID | None = None,
    min_price: Annotated[Decimal | None, Query(ge=0)] = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    location: str | None = None,
    cuisine_type: str | None = None,
    meal_category: str | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[OfferRead]:
    offers = await offer_crud.list_offers(
        db,
        restaurant_id=restaurant_id,
        only_active=True,
        min_price=min_price,
        max_price=max_price,
        location=location,
        cuisine_type=cuisine_type,
        meal_category=meal_category,
        skip=skip,
        limit=limit,
    )
    return [OfferRead.model_validate(o) for o in offers]


@router.get("/{offer_id}", response_model=OfferRead)
async def get_offer(offer_id: uuid.UUID, db: DbSession) -> OfferRead:
    offer = await offer_crud.get_by_id(db, offer_id)
    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found"
        )
    return OfferRead.model_validate(offer)


@router.post(
    "",
    response_model=OfferRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.restaurant))],
)
async def create_offer(
    payload: OfferCreate, db: DbSession, current_user: CurrentUser
) -> OfferRead:
    profile = await restaurant_crud.get_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create a restaurant profile before posting offers",
        )
    if profile.status != RestaurantStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Restaurant is not approved to post offers",
        )
    if payload.discounted_price > payload.original_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discounted price cannot exceed original price",
        )
    offer = await offer_crud.create(db, profile.id, payload)
    return OfferRead.model_validate(offer)


@router.patch(
    "/{offer_id}",
    response_model=OfferRead,
    dependencies=[Depends(require_role(UserRole.restaurant))],
)
async def update_offer(
    offer_id: uuid.UUID,
    payload: OfferUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> OfferRead:
    offer = await offer_crud.get_by_id(db, offer_id)
    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found"
        )
    profile = await restaurant_crud.get_by_user_id(db, current_user.id)
    if profile is None or offer.restaurant_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify offers for another restaurant",
        )
    new_original = payload.original_price if payload.original_price is not None else offer.original_price
    new_discounted = (
        payload.discounted_price if payload.discounted_price is not None else offer.discounted_price
    )
    if new_discounted > new_original:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discounted price cannot exceed original price",
        )
    offer = await offer_crud.update(db, offer, payload)
    return OfferRead.model_validate(offer)


@router.delete(
    "/{offer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(UserRole.restaurant))],
)
async def delete_offer(
    offer_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> None:
    offer = await offer_crud.get_by_id(db, offer_id)
    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found"
        )
    profile = await restaurant_crud.get_by_user_id(db, current_user.id)
    if profile is None or offer.restaurant_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete offers for another restaurant",
        )
    await offer_crud.delete(db, offer)
