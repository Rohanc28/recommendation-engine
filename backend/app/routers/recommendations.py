import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.schemas.recommendation import RecommendationItem
from app.services.auth import get_current_user_optional
from app.services.recommendation import get_recommendations

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("/{movie_id}", response_model=list[RecommendationItem])
async def recommend(
    movie_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    return await get_recommendations(db, movie_id, user_id, limit)
