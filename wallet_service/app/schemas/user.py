from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=80)
    email: EmailStr


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime | None

    model_config = {"from_attributes": True}
