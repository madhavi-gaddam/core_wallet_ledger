import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr


class UserRead(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}

