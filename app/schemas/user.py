from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import FreeTimeLevel, UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    has_yard: bool = False
    free_time_level: FreeTimeLevel = FreeTimeLevel.LOW
    avatar_url: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    has_yard: bool | None = None
    free_time_level: FreeTimeLevel | None = None
    avatar_url: str | None = None
    password: str | None = None


class UserPreferencesUpdate(BaseModel):
    has_yard: bool
    free_time_level: FreeTimeLevel


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole
    auth_provider: str = "local"
    google_id: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
