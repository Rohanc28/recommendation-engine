import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.similarity_vote import SimilarityVote
from app.models.movie import Movie
from app.models.user import User
from app.models.user_interaction import UserMovieInteraction
from app.schemas.recommendation import VoteCreate, VoteOut
from app.services.auth import get_current_user
from app.services.demo_cache import invalidate_recs

router = APIRouter(prefix="/api/movies/{movie_id}/votes", tags=["votes"])


@router.post("", response_model=VoteOut, status_code=status.HTTP_201_CREATED)
async def cast_vote(
    movie_id: uuid.UUID,
    payload: VoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.vote_type not in ("close", "somewhat", "different"):
        raise HTTPException(status_code=400, detail="vote_type must be close, somewhat, or different")

    if movie_id == payload.movie_id_b:
        raise HTTPException(status_code=400, detail="Cannot vote on a movie against itself")

    # Verify both movies exist
    for mid in (movie_id, payload.movie_id_b):
        m = (await db.execute(select(Movie).where(Movie.id == mid))).scalar_one_or_none()
        if not m:
            raise HTTPException(status_code=404, detail=f"Movie {mid} not found")

    # Canonical ordering to prevent symmetric duplicates
    a, b = sorted([movie_id, payload.movie_id_b], key=str)

    # Upsert: update if vote already exists
    stmt = select(SimilarityVote).where(
        SimilarityVote.movie_id_a == a,
        SimilarityVote.movie_id_b == b,
        SimilarityVote.user_id == current_user.id,
    )
    vote = (await db.execute(stmt)).scalar_one_or_none()

    if vote:
        vote.vote_type = payload.vote_type
    else:
        vote = SimilarityVote(
            movie_id_a=a,
            movie_id_b=b,
            user_id=current_user.id,
            vote_type=payload.vote_type,
        )
        db.add(vote)

    db.add(UserMovieInteraction(user_id=current_user.id, movie_id=movie_id, interaction_type="voted"))
    await db.flush()
    # Bust rec cache so community_vote scores update immediately
    invalidate_recs(str(movie_id))
    invalidate_recs(str(payload.movie_id_b))

    return VoteOut(
        id=vote.id,
        movie_id_a=vote.movie_id_a,
        movie_id_b=vote.movie_id_b,
        user_id=vote.user_id,
        vote_type=vote.vote_type,
        score=vote.score,
    )


@router.get("", response_model=list[VoteOut])
async def list_votes(movie_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """All community votes involving this movie."""
    stmt = select(SimilarityVote).where(
        (SimilarityVote.movie_id_a == movie_id) | (SimilarityVote.movie_id_b == movie_id)
    )
    votes = (await db.execute(stmt)).scalars().all()
    return [
        VoteOut(
            id=v.id, movie_id_a=v.movie_id_a, movie_id_b=v.movie_id_b,
            user_id=v.user_id, vote_type=v.vote_type, score=v.score,
        )
        for v in votes
    ]
