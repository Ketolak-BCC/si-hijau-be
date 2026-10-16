import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional, get_db
from app.models.scan import ScanHistory
from app.models.user import FreeTimeLevel, User
from app.models.waste import WasteCategoryEnum
from app.schemas.decision import DecisionResponse
from app.services.decision_service import decision_engine

router = APIRouter()


@router.get("/evaluate", response_model=DecisionResponse)
async def evaluate_decision(
    waste_category: WasteCategoryEnum,
    item_name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    has_yard: bool | None = Query(default=None),
    free_time_level: FreeTimeLevel | None = Query(default=None),
    estimated_size: str | None = Query(default=None),
    scan_id: int | None = Query(default=None),
):
    resolved_yard = has_yard if has_yard is not None else (current_user.has_yard if current_user else False)
    resolved_time = (
        free_time_level
        if free_time_level is not None
        else (current_user.free_time_level if current_user else FreeTimeLevel.LOW)
    )

    resolved_size = estimated_size
    item_specific_actions = None

    if scan_id is not None:
        scan = await db.get(ScanHistory, scan_id)
        if scan and scan.raw_analysis:
            try:
                parsed = json.loads(scan.raw_analysis)
                if isinstance(parsed, dict):
                    if not resolved_size:
                        resolved_size = parsed.get("estimated_size")
                    item_specific_actions = parsed.get("item_specific_actions")
            except Exception:
                pass

    return decision_engine.evaluate(
        waste_category=waste_category,
        item_name=item_name,
        has_yard=resolved_yard,
        free_time_level=resolved_time,
        estimated_size=resolved_size,
        item_specific_actions=item_specific_actions,
    )
