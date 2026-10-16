from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserPreferencesUpdate, UserResponse

router = APIRouter()


@router.put("/preferences", response_model=UserResponse)
async def update_preferences(
    preferences_in: UserPreferencesUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    current_user.has_yard = preferences_in.has_yard
    current_user.free_time_level = preferences_in.free_time_level
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
