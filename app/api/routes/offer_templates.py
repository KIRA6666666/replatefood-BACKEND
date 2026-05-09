import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, DbSession, require_role
from app.crud import offer_template as template_crud
from app.crud import restaurant_profile as restaurant_crud
from app.models.user import UserRole
from app.schemas.offer_template import OfferTemplateCreate, OfferTemplateRead

router = APIRouter(
    prefix="/offer-templates",
    tags=["offer-templates"],
    dependencies=[Depends(require_role(UserRole.restaurant))],
)


@router.get("", response_model=list[OfferTemplateRead])
async def list_templates(db: DbSession, current_user: CurrentUser) -> list[OfferTemplateRead]:
    profile = await restaurant_crud.get_by_user_id(db, current_user.id)
    if profile is None:
        return []
    templates = await template_crud.list_by_restaurant(db, profile.id)
    return [OfferTemplateRead.model_validate(t) for t in templates]


@router.post("", response_model=OfferTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: OfferTemplateCreate, db: DbSession, current_user: CurrentUser
) -> OfferTemplateRead:
    profile = await restaurant_crud.get_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No restaurant profile")
    if payload.discounted_price > payload.original_price:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Discounted price cannot exceed original price")
    template = await template_crud.create(db, profile.id, payload)
    return OfferTemplateRead.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> None:
    template = await template_crud.get_by_id(db, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    profile = await restaurant_crud.get_by_user_id(db, current_user.id)
    if profile is None or template.restaurant_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your template")
    await template_crud.delete(db, template)
