from pydantic import BaseModel

from app.models.waste import ActionTypeEnum, DifficultyEnum, WasteCategoryEnum


class DecisionOption(BaseModel):
    action_type: ActionTypeEnum
    title: str
    description: str
    difficulty: DifficultyEnum
    estimated_time: str
    guide_id: int | None = None
    is_primary_recommendation: bool = False


class DecisionResponse(BaseModel):
    waste_category: WasteCategoryEnum
    item_name: str
    user_context: dict
    primary_action: ActionTypeEnum
    recommendations: list[DecisionOption]
    item_specific_action_points: list[str] = []
    physical_feasibility_notes: str | None = None
