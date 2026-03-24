import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.review import Review
from app.models.movie import Movie
from app.models.user import User
from app.models.user_interaction import UserMovieInteraction
from app.schemas.review import ReviewCreate, ReviewOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/movies/{movie_id}/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewOut])
async def list_reviews(movie_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Review).where(Review.movie_id == movie_id)
    reviews = (await db.execute(stmt)).scalars().all()
    out = []
    for r in reviews:
        await db.refresh(r, ["user"])
        d = ReviewOut.model_validate(r)
        d.username = r.user.username if r.user else ""
        out.append(d)
    return out


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    movie_id: uuid.UUID,
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify movie exists
    movie = (await db.execute(select(Movie).where(Movie.id == movie_id))).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # One review per user per movie
    existing = (await db.execute(
        select(Review).where(Review.movie_id == movie_id, Review.user_id == current_user.id)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="You have already reviewed this movie")

    review = Review(
        movie_id=movie_id,
        user_id=current_user.id,
        content=payload.content,
        rating=payload.rating,
    )
    db.add(review)
    db.add(UserMovieInteraction(user_id=current_user.id, movie_id=movie_id, interaction_type="reviewed"))
    await db.flush()

    d = ReviewOut.model_validate(review)
    d.username = current_user.username
    return d


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    movie_id: uuid.UUID,
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Review).where(Review.id == review_id, Review.movie_id == movie_id)
    review = (await db.execute(stmt)).scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your review")
    await db.delete(review)
