from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.action_log import ActionLog
from app.models.user import User
from app.schemas.action_log import (
    ActionLogCreate,
    ActionLogResponse,
    ImpactSummaryResponse,
)

router = APIRouter()


@router.post("", response_model=ActionLogResponse, status_code=status.HTTP_201_CREATED)
async def create_action_log(
    log_in: ActionLogCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    action_log = ActionLog(
        user_id=current_user.id,
        scan_id=log_in.scan_id,
        action_type=log_in.action_type.value,
        waste_category=log_in.waste_category.value,
        partner_id=log_in.partner_id,
        quantity_desc=log_in.quantity_desc,
        notes=log_in.notes,
    )
    db.add(action_log)
    await db.commit()
    await db.refresh(action_log)
    return action_log


@router.get("", response_model=list[ActionLogResponse])
async def list_user_action_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
):
    query = (
        select(ActionLog)
        .where(ActionLog.user_id == current_user.id)
        .order_by(desc(ActionLog.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/summary", response_model=ImpactSummaryResponse)
async def get_user_impact_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    query = select(ActionLog).where(ActionLog.user_id == current_user.id)
    result = await db.execute(query)
    logs = result.scalars().all()

    action_counts = Counter(log.action_type for log in logs)
    category_counts = Counter(log.waste_category for log in logs)

    return ImpactSummaryResponse(
        total_actions=len(logs),
        total_by_action_type=dict(action_counts),
        total_by_category=dict(category_counts),
    )
