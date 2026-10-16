from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.models.guide import ProcessingGuide
from app.models.user import User
from app.models.waste import WasteCategoryEnum
from app.schemas.guide import GuideCreate, GuideResponse

router = APIRouter()


@router.get("", response_model=list[GuideResponse])
async def list_guides(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: WasteCategoryEnum | None = Query(default=None),
):
    query = select(ProcessingGuide)
    if category:
        query = query.where(ProcessingGuide.waste_category == category.value)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{guide_id}", response_model=GuideResponse)
async def get_guide(guide_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(ProcessingGuide).where(ProcessingGuide.id == guide_id))
    guide = result.scalars().first()
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing guide not found")
    return guide


@router.post("", response_model=GuideResponse, status_code=status.HTTP_201_CREATED)
async def create_guide(
    guide_in: GuideCreate,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    guide_dict = guide_in.model_dump()
    guide_dict["waste_category"] = guide_in.waste_category.value
    guide_dict["difficulty"] = guide_in.difficulty.value
    guide_dict["steps"] = [step.model_dump() for step in guide_in.steps]

    guide = ProcessingGuide(**guide_dict)
    db.add(guide)
    await db.commit()
    await db.refresh(guide)
    return guide
