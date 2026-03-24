from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.tag import Tag
from app.models.movie import movie_tags
from app.schemas.tag import TagSearchOut

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagSearchOut])
async def search_tags(
    q: str = Query("", description="Search tags by name prefix"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Tag, func.count(movie_tags.c.movie_id).label("movie_count"))
        .outerjoin(movie_tags, Tag.id == movie_tags.c.tag_id)
        .group_by(Tag.id)
        .order_by(func.count(movie_tags.c.movie_id).desc())
        .limit(limit)
    )
    if q:
        stmt = stmt.where(Tag.name.ilike(f"{q}%"))

    rows = (await db.execute(stmt)).all()
    return [
        TagSearchOut(id=r[0].id, name=r[0].name, slug=r[0].slug, movie_count=r[1])
        for r in rows
    ]
