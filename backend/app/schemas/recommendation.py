import uuid
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.tag import TagOut


class RecommendationItem(BaseModel):
    movie_id: uuid.UUID
    title: str
    description: Optional[str]
    year: Optional[int]
    poster_url: Optional[str]
    tags: List[TagOut] = []
    avg_rating: Optional[float] = None

    # Score breakdown
    final_score: float
    embedding_score: float      # cosine similarity (weight 0.50)
    tag_score: float            # jaccard similarity  (weight 0.20)
    user_pref_score: float      # user preference     (weight 0.20)
    community_vote_score: float # community votes     (weight 0.10)

    # Community vote distribution
    vote_counts: dict = {}      # {"close": N, "somewhat": N, "different": N}

    model_config = {"from_attributes": True}


class VoteCreate(BaseModel):
    movie_id_b: uuid.UUID
    vote_type: str

    def __init__(self, **data):
        super().__init__(**data)
        if self.vote_type not in ("close", "somewhat", "different"):
            raise ValueError("vote_type must be close, somewhat, or different")


class VoteOut(BaseModel):
    id: uuid.UUID
    movie_id_a: uuid.UUID
    movie_id_b: uuid.UUID
    user_id: uuid.UUID
    vote_type: str
    score: float

    model_config = {"from_attributes": True}
