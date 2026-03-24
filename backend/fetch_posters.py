"""
Fetch movie poster URLs from Wikipedia's free public API — no API key needed.

How it works
------------
Wikipedia's /w/api.php returns the infobox thumbnail for any article.
We try several search terms in order until we find a poster:
  1. "{title} ({year} film)"       e.g. "Inception (2010 film)"
  2. "{title} film"                e.g. "Jawan film"
  3. "{title}"                     plain title fallback

Concurrency: 20 parallel requests (Wikipedia allows up to 200/s).
Speed: ~2200 movies in ~90 seconds.

Usage
-----
    cd backend
    source venv/Scripts/activate     # Windows: venv\Scripts\activate
    python fetch_posters.py

    # Limit to first N movies (useful for testing):
    python fetch_posters.py --limit 50

    # Re-fetch even movies that already have a poster:
    python fetch_posters.py --overwrite
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import httpx

WIKI_API    = "https://en.wikipedia.org/w/api.php"
CONCURRENCY = 20
BATCH_SIZE  = 200
TIMEOUT     = 10.0
HEADERS     = {"User-Agent": "MovieRecommenderDemo/1.0 (movie-recommender demo app)"}

SCRIPT_DIR = Path(__file__).parent


# ── Wikipedia lookup ──────────────────────────────────────────────────────────

async def get_poster_url(
    client: httpx.AsyncClient, title: str, year: int | None
) -> str | None:
    """Try multiple search terms; return first poster URL found."""
    candidates = []
    if year:
        candidates.append(f"{title} ({year} film)")
    candidates.append(f"{title} film")
    candidates.append(title)

    for term in candidates:
        try:
            r = await client.get(
                WIKI_API,
                params={
                    "action": "query",
                    "titles": term,
                    "prop": "pageimages",
                    "format": "json",
                    "pithumbsize": 500,
                    "pilicense": "any",
                    "redirects": 1,
                },
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            pages = r.json().get("query", {}).get("pages", {})
            for page in pages.values():
                thumb = page.get("thumbnail", {}).get("source")
                if thumb:
                    return thumb
        except Exception:
            continue
    return None


# ── main ──────────────────────────────────────────────────────────────────────

async def main(limit: int | None, overwrite: bool) -> None:
    from app.database import AsyncSessionLocal, init_db
    from app.models.movie import Movie
    from sqlalchemy import select, update

    await init_db()

    async with AsyncSessionLocal() as db:
        stmt = select(Movie.id, Movie.title, Movie.year)
        if not overwrite:
            stmt = stmt.where((Movie.poster_url == None) | (Movie.poster_url == ""))
        if limit:
            stmt = stmt.limit(limit)
        rows = (await db.execute(stmt)).all()

    total = len(rows)
    print(f"Movies to process: {total}")
    if not total:
        print("Nothing to do.")
        return

    semaphore  = asyncio.Semaphore(CONCURRENCY)
    updates: dict[str, str] = {}
    found = 0
    not_found = 0

    async def process(movie_id, title, year):
        nonlocal found, not_found
        async with semaphore:
            url = await get_poster_url(client, title, year)
            if url:
                updates[str(movie_id)] = url
                found += 1
            else:
                not_found += 1

            done = found + not_found
            if done % 200 == 0 or done == total:
                pct = done / total * 100
                print(f"  {done}/{total} ({pct:.0f}%)  found={found}  not_found={not_found}")

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[process(r.id, r.title, r.year) for r in rows])

    hit_rate = found / total * 100 if total else 0
    print(f"\nLookup complete: {found}/{total} found ({hit_rate:.0f}% hit rate)")

    if not updates:
        print("Nothing to write.")
        return

    print(f"Writing {len(updates)} URLs to DB …")
    ids = list(updates.keys())
    async with AsyncSessionLocal() as db:
        for i in range(0, len(ids), BATCH_SIZE):
            batch = ids[i : i + BATCH_SIZE]
            for mid in batch:
                await db.execute(
                    update(Movie).where(Movie.id == mid).values(poster_url=updates[mid])
                )
            await db.commit()
            print(f"  Committed {min(i + BATCH_SIZE, len(ids))}/{len(ids)}")

    print(f"\nDone! {len(updates)} poster URLs saved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Wikipedia poster URLs (no API key needed)")
    parser.add_argument("--limit",     type=int, default=None, help="Only process first N movies")
    parser.add_argument("--overwrite", action="store_true",    help="Re-fetch even movies with existing posters")
    args = parser.parse_args()

    os.chdir(SCRIPT_DIR)
    asyncio.run(main(args.limit, args.overwrite))
