import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator


class ReviewCreate(BaseModel):
    content: str
    rating: int

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Review must be at least 10 characters")
        return v

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("Rating must be 1–5")
        return v


class ReviewOut(BaseModel):
    id: uuid.UUID
    movie_id: uuid.UUID
    user_id: uuid.UUID
    username: str = ""
    content: str
    rating: int
    created_at: datetime

    model_config = {"from_attributes": True}
