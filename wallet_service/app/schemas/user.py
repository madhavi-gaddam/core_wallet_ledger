from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=80)
    password: str = Field(..., min_length=8, max_length=128)
    email: EmailStr | None = None


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr | None
    created_at: datetime | None

    model_config = {"from_attributes": True}
