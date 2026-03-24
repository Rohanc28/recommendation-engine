"""Tag normalisation and upsert helpers."""
import re
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tag import Tag


def normalize_tag(raw: str) -> tuple[str, str]:
    """Return (name, slug) from raw user input.

    name: lowercase, stripped, inner-spaces collapsed to single space
    slug: name with spaces replaced by hyphens
    """
    name = re.sub(r"\s+", " ", raw.strip().lower())
    slug = name.replace(" ", "-")
    return name, slug


async def get_or_create_tags(session: AsyncSession, raw_tags: List[str]) -> List[Tag]:
    """Normalise raw tag strings and upsert into DB; return Tag objects."""
    results: List[Tag] = []
    seen_slugs: set[str] = set()

    for raw in raw_tags:
        name, slug = normalize_tag(raw)
        if not name or slug in seen_slugs:
            continue
        seen_slugs.add(slug)

        stmt = select(Tag).where(Tag.slug == slug)
        tag = (await session.execute(stmt)).scalar_one_or_none()

        if tag is None:
            tag = Tag(name=name, slug=slug)
            session.add(tag)
            await session.flush()  # get id before commit

        results.append(tag)

    return results
