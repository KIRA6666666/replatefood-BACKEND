import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.offer_template import OfferTemplate
from app.schemas.offer_template import OfferTemplateCreate


async def list_by_restaurant(db: AsyncSession, restaurant_id: uuid.UUID) -> list[OfferTemplate]:
    result = await db.execute(
        select(OfferTemplate)
        .where(OfferTemplate.restaurant_id == restaurant_id)
        .order_by(OfferTemplate.created_at.desc())
    )
    return list(result.scalars().all())


async def create(db: AsyncSession, restaurant_id: uuid.UUID, payload: OfferTemplateCreate) -> OfferTemplate:
    template = OfferTemplate(restaurant_id=restaurant_id, **payload.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def get_by_id(db: AsyncSession, template_id: uuid.UUID) -> OfferTemplate | None:
    return await db.get(OfferTemplate, template_id)


async def delete(db: AsyncSession, template: OfferTemplate) -> None:
    await db.delete(template)
    await db.commit()
