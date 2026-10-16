from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.waste import DifficultyEnum, WasteCategoryEnum


class GuideStep(BaseModel):
    step_number: int
    title: str
    instruction: str


class GuideCreate(BaseModel):
    waste_category: WasteCategoryEnum
    title: str
    summary: str
    difficulty: DifficultyEnum
    estimated_time: str
    steps: list[GuideStep]


class GuideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    waste_category: str
    title: str
    summary: str
    difficulty: str
    estimated_time: str
    steps: list[dict]
    created_at: datetime
