import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
from app.models.movie import Movie
from app.models.review import Review
from app.models.user_interaction import UserMovieInteraction
from app.models.user import User
from app.schemas.movie import MovieCreate, MovieUpdate, MovieOut, MovieListOut
from app.services.auth import get_current_user, get_current_user_optional
from app.services.tag import get_or_create_tags
from app.services.embedding import get_embedding_service
from app.services.demo_cache import invalidate_embedding, invalidate_recs

router = APIRouter(prefix="/api/movies", tags=["movies"])


@router.get("", response_model=list[MovieListOut])
async def list_movies(
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None, description="Filter by tag slug"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Movie)
    if search:
        stmt = stmt.where(Movie.title.ilike(f"%{search}%"))
    if tag:
        from app.models.tag import Tag
        from app.models.movie import movie_tags
        stmt = stmt.join(movie_tags).join(Tag).where(Tag.slug == tag)

    stmt = stmt.order_by(desc(Movie.created_at)).offset((page - 1) * size).limit(size)
    movies = (await db.execute(stmt)).scalars().all()

    movie_ids = [m.id for m in movies]
    rating_map = await _avg_ratings(db, movie_ids)

    out = []
    for m in movies:
        d = MovieListOut.model_validate(m)
        d.avg_rating = rating_map.get(m.id)
        d.review_count = await _review_count(db, m.id)
        out.append(d)
    return out


@router.post("", response_model=MovieOut, status_code=status.HTTP_201_CREATED)
async def create_movie(
    payload: MovieCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tags = await get_or_create_tags(db, payload.tags)
    emb_svc = get_embedding_service()
    embedding = emb_svc.encode_movie(
        title=payload.title,
        description=payload.description,
        tags=[t.name for t in tags],
    )

    movie = Movie(
        title=payload.title,
        description=payload.description,
        year=payload.year,
        poster_url=payload.poster_url,
        embedding=embedding,
        created_by=current_user.id,
        tags=tags,
    )
    db.add(movie)
    await db.flush()
    db.add(UserMovieInteraction(user_id=current_user.id, movie_id=movie.id, interaction_type="added"))
    await db.flush()
    return MovieOut.model_validate(movie)


@router.get("/{movie_id}", response_model=MovieOut)
async def get_movie(
    movie_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    stmt = select(Movie).where(Movie.id == movie_id)
    movie = (await db.execute(stmt)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if current_user:
        db.add(UserMovieInteraction(
            user_id=current_user.id, movie_id=movie.id, interaction_type="viewed"
        ))
        await db.flush()

    rating_map = await _avg_ratings(db, [movie.id])
    out = MovieOut.model_validate(movie)
    out.avg_rating = rating_map.get(movie.id)
    out.review_count = await _review_count(db, movie.id)
    return out


@router.patch("/{movie_id}", response_model=MovieOut)
async def update_movie(
    movie_id: uuid.UUID,
    payload: MovieUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Movie).where(Movie.id == movie_id)
    movie = (await db.execute(stmt)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if movie.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not the movie creator")

    content_changed = False
    if payload.title is not None:
        movie.title = payload.title
        content_changed = True
    if payload.description is not None:
        movie.description = payload.description
        content_changed = True
    if payload.year is not None:
        movie.year = payload.year
    if payload.poster_url is not None:
        movie.poster_url = payload.poster_url

    if payload.tags is not None:
        movie.tags = await get_or_create_tags(db, payload.tags)
        content_changed = True

    # In demo mode skip the expensive embedding recomputation unless explicitly needed
    if content_changed and not settings.DEMO_MODE:
        emb_svc = get_embedding_service()
        movie.embedding = emb_svc.encode_movie(
            movie.title, movie.description, [t.name for t in movie.tags]
        )
        invalidate_embedding(str(movie_id))
        invalidate_recs(str(movie_id))
    elif content_changed and settings.DEMO_MODE:
        # Just bust the rec cache so stale results aren't served
        invalidate_recs(str(movie_id))

    await db.flush()
    return MovieOut.model_validate(movie)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Movie).where(Movie.id == movie_id)
    movie = (await db.execute(stmt)).scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if movie.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not the movie creator")
    invalidate_embedding(str(movie_id))
    invalidate_recs(str(movie_id))
    await db.delete(movie)


# ── helpers ───────────────────────────────────────────────────────────────────

async def _avg_ratings(db: AsyncSession, movie_ids: list) -> dict:
    if not movie_ids:
        return {}
    rows = (
        await db.execute(
            select(Review.movie_id, func.avg(Review.rating).label("avg"))
            .where(Review.movie_id.in_(movie_ids))
            .group_by(Review.movie_id)
        )
    ).all()
    return {r[0]: round(float(r[1]), 2) for r in rows}


async def _review_count(db: AsyncSession, movie_id: uuid.UUID) -> int:
    return (await db.execute(
        select(func.count()).select_from(Review).where(Review.movie_id == movie_id)
    )).scalar() or 0
