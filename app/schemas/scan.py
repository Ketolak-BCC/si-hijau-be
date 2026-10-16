import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.waste import WasteCategoryEnum


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    item_name: str
    detected_category: str
    confidence_score: float
    raw_analysis: str | None = None
    created_at: datetime
    estimated_size: str | None = None
    physical_condition: str | None = None
    material_type: str | None = None
    item_specific_actions: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def populate_extracted_fields(cls, data: Any) -> Any:
        raw = getattr(data, "raw_analysis", None) if not isinstance(data, dict) else data.get("raw_analysis")
        if raw and isinstance(raw, str) and raw.strip().startswith("{"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    if not isinstance(data, dict):
                        return {
                            "id": data.id,
                            "image_url": data.image_url,
                            "item_name": data.item_name,
                            "detected_category": data.detected_category,
                            "confidence_score": data.confidence_score,
                            "raw_analysis": data.raw_analysis,
                            "created_at": data.created_at,
                            "estimated_size": parsed.get("estimated_size"),
                            "physical_condition": parsed.get("physical_condition"),
                            "material_type": parsed.get("material_type"),
                            "item_specific_actions": parsed.get("item_specific_actions", []),
                        }
                    else:
                        data.setdefault("estimated_size", parsed.get("estimated_size"))
                        data.setdefault("physical_condition", parsed.get("physical_condition"))
                        data.setdefault("material_type", parsed.get("material_type"))
                        data.setdefault("item_specific_actions", parsed.get("item_specific_actions", []))
            except Exception:
                pass
        return data


class ScanCreateManual(BaseModel):
    item_name: str
    detected_category: WasteCategoryEnum
    image_url: str
    confidence_score: float = 1.0
