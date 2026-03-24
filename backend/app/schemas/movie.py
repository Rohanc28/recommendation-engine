import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator
from app.schemas.tag import TagOut


class MovieCreate(BaseModel):
    title: str
    description: Optional[str] = None
    year: Optional[int] = None
    poster_url: Optional[str] = None
    # 3–5 tag names (raw input, service layer normalizes)
    tags: List[str]

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("tags")
    @classmethod
    def tags_count(cls, v: List[str]) -> List[str]:
        cleaned = [t.strip() for t in v if t.strip()]
        if len(cleaned) < 3 or len(cleaned) > 5:
            raise ValueError("Provide 3–5 tags")
        return cleaned

    @field_validator("year")
    @classmethod
    def year_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1888 <= v <= 2100):
            raise ValueError("Year must be between 1888 and 2100")
        return v


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    year: Optional[int] = None
    poster_url: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("tags")
    @classmethod
    def tags_count(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            cleaned = [t.strip() for t in v if t.strip()]
            if len(cleaned) < 3 or len(cleaned) > 5:
                raise ValueError("Provide 3–5 tags")
            return cleaned
        return v


class MovieOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    year: Optional[int]
    poster_url: Optional[str]
    tags: List[TagOut] = []
    created_by: Optional[uuid.UUID]
    created_at: datetime
    avg_rating: Optional[float] = None
    review_count: int = 0

    model_config = {"from_attributes": True}


class MovieListOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    year: Optional[int]
    poster_url: Optional[str]
    tags: List[TagOut] = []
    avg_rating: Optional[float] = None
    review_count: int = 0

    model_config = {"from_attributes": True}
