from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.waste import ActionTypeEnum, WasteCategoryEnum


class ActionLogCreate(BaseModel):
    scan_id: int | None = None
    action_type: ActionTypeEnum
    waste_category: WasteCategoryEnum
    partner_id: int | None = None
    quantity_desc: str | None = None
    notes: str | None = None


class ActionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    scan_id: int | None = None
    action_type: str
    waste_category: str
    partner_id: int | None = None
    quantity_desc: str | None = None
    notes: str | None = None
    created_at: datetime


class ImpactSummaryResponse(BaseModel):
    total_actions: int
    total_by_action_type: dict[str, int]
    total_by_category: dict[str, int]
