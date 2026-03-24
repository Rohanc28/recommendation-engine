"""
Seed the database from data/IMDB-Movie-Dataset(2023-1951).csv.

Strategy
--------
- Tags come from the genre column (already normalised to lowercase slugs).
- Movies with <3 genres are padded with a decade tag (e.g. "2010s") and,
  if still short, "cinema".
- All movie embeddings are computed in one batched call — much faster than
  per-request HTTP.
- Skips rows whose title already exists in the DB.
- Creates / reuses a seed user (seeder@cinematch.local / seedpass123).

Usage
-----
    cd backend
    source venv/Scripts/activate   # Windows: venv\Scripts\activate
    python seed.py
"""
import asyncio
import csv
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ── resolve CSV path ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
CSV_PATH = SCRIPT_DIR.parent / "data" / "IMDB-Movie-Dataset(2023-1951).csv"

if not CSV_PATH.exists():
    sys.exit(f"CSV not found: {CSV_PATH}")


# ── helpers ───────────────────────────────────────────────────────────────────

def decade_tag(year_str: str) -> str:
    try:
        y = int(year_str)
        return f"{(y // 10) * 10}s"
    except (ValueError, TypeError):
        return "cinema"


def build_tags(genre_str: str, year_str: str) -> list[str]:
    """
    Returns 3–5 lowercase slug tags.
    Source is the genre field; padded with decade and 'cinema' if needed.
    """
    raw = [g.strip().lower() for g in genre_str.split(",") if g.strip()]
    slugs = [re.sub(r"[^a-z0-9]+", "-", g).strip("-") for g in raw]
    slugs = list(dict.fromkeys(slugs))  # deduplicate, preserve order

    if len(slugs) < 3:
        dec = decade_tag(year_str)
        if dec not in slugs:
            slugs.append(dec)
    if len(slugs) < 3:
        if "cinema" not in slugs:
            slugs.append("cinema")

    return slugs[:5]


def parse_year(year_str) -> int | None:
    try:
        return int(year_str)
    except (ValueError, TypeError):
        return None


# ── main ──────────────────────────────────────────────────────────────────────

async def main():
    # Import app modules after the working directory is set
    from app.database import AsyncSessionLocal, init_db
    from app.models.user import User
    from app.models.movie import Movie
    from app.models.tag import Tag
    from app.models.movie import movie_tags as movie_tags_table
    from app.utils.security import hash_password
    from app.services.embedding import get_embedding_service
    from sqlalchemy import select, insert

    print("Initialising DB …")
    await init_db()

    # ── load CSV ──────────────────────────────────────────────────────────────
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("movie_name", "").strip()
            if not title:
                continue
            rows.append(row)

    print(f"CSV rows loaded: {len(rows)}")

    async with AsyncSessionLocal() as db:
        # ── seed user ─────────────────────────────────────────────────────────
        SEED_EMAIL = "seeder@cinematch.demo"
        seeder = (await db.execute(
            select(User).where(User.email == SEED_EMAIL)
        )).scalar_one_or_none()

        if seeder is None:
            seeder = User(
                username="seeder",
                email=SEED_EMAIL,
                hashed_password=hash_password("seedpass123"),
            )
            db.add(seeder)
            await db.flush()
            print(f"Created seed user: {seeder.username}")
        else:
            print(f"Using existing seed user: {seeder.username}")

        # ── find already-seeded titles ────────────────────────────────────────
        existing_titles: set[str] = set(
            (await db.execute(select(Movie.title))).scalars().all()
        )
        print(f"Movies already in DB: {len(existing_titles)}")

        pending = [r for r in rows if r["movie_name"].strip() not in existing_titles]
        print(f"Movies to insert: {len(pending)}")

        if not pending:
            print("Nothing to do — all movies already seeded.")
            return

        # ── batch-encode embeddings ───────────────────────────────────────────
        print("Loading embedding model …")
        emb_svc = get_embedding_service()

        texts = []
        for r in pending:
            tag_names = build_tags(r.get("genre", ""), r.get("year", ""))
            parts = [r["movie_name"].strip()]
            overview = r.get("overview", "").strip()
            if overview:
                parts.append(overview)
            parts.append(" ".join(tag_names))
            texts.append(". ".join(parts))

        print(f"Encoding {len(texts)} embeddings in one batch …")
        import numpy as np
        embeddings: np.ndarray = emb_svc.encode(texts)   # shape (N, 384)
        print("Embeddings done.")

        # ── upsert tags ───────────────────────────────────────────────────────
        print("Upserting tags …")
        tag_cache: dict[str, Tag] = {}

        # Collect all unique slugs first
        all_slugs: set[str] = set()
        pending_tags: list[list[str]] = []
        for r in pending:
            tags = build_tags(r.get("genre", ""), r.get("year", ""))
            pending_tags.append(tags)
            all_slugs.update(tags)

        existing_tags = (await db.execute(
            select(Tag).where(Tag.slug.in_(all_slugs))
        )).scalars().all()
        tag_cache = {t.slug: t for t in existing_tags}

        new_slugs = all_slugs - tag_cache.keys()
        for slug in new_slugs:
            name = slug.replace("-", " ")
            t = Tag(name=name, slug=slug)
            db.add(t)
            tag_cache[slug] = t

        await db.flush()
        print(f"  Tags in DB: {len(tag_cache)} ({len(new_slugs)} new)")

        # ── insert movies + movie_tags ─────────────────────────────────────────
        print("Inserting movies …")
        now = datetime.now(timezone.utc)
        batch_size = 100
        inserted = 0

        for i, (r, emb, tags) in enumerate(zip(pending, embeddings, pending_tags)):
            title    = r["movie_name"].strip()
            year     = parse_year(r.get("year"))
            overview = r.get("overview", "").strip() or None

            movie_id = uuid.uuid4()
            movie = Movie(
                id=movie_id,
                title=title,
                description=overview,
                year=year,
                embedding=emb.tolist(),
                created_by=seeder.id,
            )
            db.add(movie)
            await db.flush()  # write movie row, get id confirmed

            # Insert junction rows directly — avoids async lazy-load on relationship
            tag_rows = [
                {"movie_id": movie_id, "tag_id": tag_cache[slug].id}
                for slug in tags if slug in tag_cache
            ]
            if tag_rows:
                await db.execute(movie_tags_table.insert(), tag_rows)

            inserted += 1

            # Commit in batches to keep transaction size manageable
            if inserted % batch_size == 0:
                await db.commit()
                pct = inserted / len(pending) * 100
                print(f"  {inserted}/{len(pending)} ({pct:.0f}%) …")

        await db.commit()
        print(f"\nDone! {inserted} movies inserted.")


if __name__ == "__main__":
    os.chdir(SCRIPT_DIR)
    asyncio.run(main())
