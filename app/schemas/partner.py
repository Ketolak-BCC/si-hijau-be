from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PartnerBase(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    accepted_categories: str
    phone_number: str
    operational_hours: str
    capacity_info: str
    requirements: str | None = None
    is_active: bool = True


class PartnerCreate(PartnerBase):
    pass


class PartnerUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    accepted_categories: str | None = None
    phone_number: str | None = None
    operational_hours: str | None = None
    capacity_info: str | None = None
    requirements: str | None = None
    is_active: bool | None = None


class PartnerResponse(PartnerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    distance_km: float | None = None
