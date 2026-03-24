import uuid
from datetime import datetime
from pydantic import BaseModel


class TagOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TagSearchOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    movie_count: int = 0

    model_config = {"from_attributes": True}
