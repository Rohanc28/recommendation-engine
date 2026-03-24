"""
Hybrid recommendation engine — SQLite / numpy edition.

final_score = (embedding_sim * 0.50)   ← numpy cosine (dot-product of L2-normed vecs)
            + (tag_score      * 0.20)   ← Jaccard similarity of tag sets
            + (user_pref      * 0.20)   ← tag overlap with user interaction history
            + (community_vote * 0.10)   ← avg community vote score

Demo mode: results are memoised per source movie for DEMO_REC_CACHE_TTL seconds so
repeated calls to the same endpoint don't re-run the full numpy pass.
"""
from __future__ import annotations
import uuid
import logging
from typing import List, Optional
import numpy as np
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.movie import Movie
from app.models.similarity_vote import SimilarityVote
from app.models.user_interaction import UserMovieInteraction
from app.models.review import Review
from app.services import demo_cache

logger = logging.getLogger(__name__)

W_EMBED = 0.50
W_TAG   = 0.20
W_PREF  = 0.20
W_VOTE  = 0.10

VOTE_SCORES = {"close": 1.0, "somewhat": 0.5, "different": 0.0}


async def get_recommendations(
    db: AsyncSession,
    movie_id: uuid.UUID,
    current_user_id: Optional[uuid.UUID] = None,
    limit: int = 10,
) -> List[dict]:
    mid_str = str(movie_id)
    # Cache key includes user so per-user preference scores don't bleed across users
    cache_key = f"{mid_str}:{current_user_id or 'anon'}"

    # ── Demo cache hit ────────────────────────────────────────────────────────
    if settings.DEMO_MODE:
        cached = demo_cache.get_cached_recs(cache_key)
        if cached is not None:
            return cached[:limit]

    # ── 1. Load source movie ──────────────────────────────────────────────────
    source: Movie | None = (
        await db.execute(select(Movie).where(Movie.id == movie_id))
    ).scalar_one_or_none()

    if source is None or source.embedding is None:
        return []

    source_vec = _get_vec(source, mid_str)
    source_tag_ids = {t.id for t in source.tags}

    # ── 2. Load all candidate movies (with embeddings) ────────────────────────
    stmt = select(Movie).where(Movie.id != movie_id, Movie.embedding.isnot(None))
    candidates: List[Movie] = (await db.execute(stmt)).scalars().all()

    if not candidates:
        return []

    # ── 3. Numpy cosine similarity (dot product; vecs are already L2-normed) ──
    cand_vecs = np.array(
        [_get_vec(m, str(m.id)) for m in candidates], dtype=np.float32
    )                                           # shape (N, DIM)
    sims = cand_vecs @ source_vec               # shape (N,)

    # Keep top-50 candidates for the remaining scoring steps
    top_n = min(50, len(candidates))
    top_idx = np.argpartition(sims, -top_n)[-top_n:]
    top_idx = top_idx[np.argsort(sims[top_idx])[::-1]]

    top_movies  = [candidates[i] for i in top_idx]
    top_sims    = [float(sims[i]) for i in top_idx]
    cand_ids    = [m.id for m in top_movies]
    movie_map   = {m.id: m for m in top_movies}
    emb_map     = {m.id: s for m, s in zip(top_movies, top_sims)}

    # ── 4. Community votes ────────────────────────────────────────────────────
    vote_map = await _community_vote_scores(db, movie_id, cand_ids)

    # ── 5. Tag Jaccard ────────────────────────────────────────────────────────
    tag_map = _tag_jaccard(source_tag_ids, movie_map)

    # ── 6. User preference ────────────────────────────────────────────────────
    pref_map = (
        await _user_pref_scores(db, current_user_id, movie_map)
        if current_user_id
        else {mid: 0.0 for mid in cand_ids}
    )

    # ── 7. Average ratings ────────────────────────────────────────────────────
    rating_map = await _avg_ratings(db, cand_ids)

    # ── 8. Compute hybrid scores ──────────────────────────────────────────────
    results = []
    for mid in cand_ids:
        emb  = emb_map.get(mid, 0.0)
        tag  = tag_map.get(mid, 0.0)
        pref = pref_map.get(mid, 0.0)
        vote = vote_map.get(mid, {}).get("avg", 0.0)

        final = (emb * W_EMBED) + (tag * W_TAG) + (pref * W_PREF) + (vote * W_VOTE)

        m = movie_map[mid]
        results.append({
            "movie_id": mid,
            "title": m.title,
            "description": m.description,
            "year": m.year,
            "poster_url": m.poster_url,
            "tags": m.tags,
            "avg_rating": rating_map.get(mid),
            "final_score": round(final, 4),
            "embedding_score": round(emb, 4),
            "tag_score": round(tag, 4),
            "user_pref_score": round(pref, 4),
            "community_vote_score": round(vote, 4),
            "vote_counts": vote_map.get(mid, {}).get("counts", {}),
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)

    if settings.DEMO_MODE:
        demo_cache.set_cached_recs(cache_key, results)

    return results[:limit]


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_vec(movie: Movie, mid_str: str) -> np.ndarray:
    """Return embedding as numpy array, using demo cache when enabled."""
    if settings.DEMO_MODE:
        cached = demo_cache.get_cached_embedding(mid_str)
        if cached is not None:
            return cached
    vec = np.array(movie.embedding, dtype=np.float32)
    if settings.DEMO_MODE:
        demo_cache.set_cached_embedding(mid_str, movie.embedding)
    return vec


def _tag_jaccard(source_tag_ids: set, movie_map: dict) -> dict:
    scores = {}
    for mid, movie in movie_map.items():
        cand_ids = {t.id for t in movie.tags}
        union = len(source_tag_ids | cand_ids)
        scores[mid] = len(source_tag_ids & cand_ids) / union if union else 0.0
    return scores


async def _community_vote_scores(
    db: AsyncSession, movie_id: uuid.UUID, candidate_ids: List[uuid.UUID]
) -> dict:
    if not candidate_ids:
        return {}
    stmt = select(SimilarityVote).where(
        (
            (SimilarityVote.movie_id_a == movie_id) &
            (SimilarityVote.movie_id_b.in_(candidate_ids))
        ) | (
            (SimilarityVote.movie_id_b == movie_id) &
            (SimilarityVote.movie_id_a.in_(candidate_ids))
        )
    )
    votes = (await db.execute(stmt)).scalars().all()

    by_pair: dict[uuid.UUID, list] = {}
    for v in votes:
        other = v.movie_id_b if v.movie_id_a == movie_id else v.movie_id_a
        by_pair.setdefault(other, []).append(v.vote_type)

    result = {}
    for mid, vote_types in by_pair.items():
        counts = {"close": 0, "somewhat": 0, "different": 0}
        for vt in vote_types:
            counts[vt] += 1
        result[mid] = {
            "avg": sum(VOTE_SCORES[vt] for vt in vote_types) / len(vote_types),
            "counts": counts,
        }
    return result


async def _user_pref_scores(
    db: AsyncSession, user_id: uuid.UUID, movie_map: dict
) -> dict:
    interacted_ids = (
        await db.execute(
            select(UserMovieInteraction.movie_id)
            .where(UserMovieInteraction.user_id == user_id)
            .distinct()
        )
    ).scalars().all()

    if not interacted_ids:
        return {mid: 0.0 for mid in movie_map}

    interacted = (
        await db.execute(select(Movie).where(Movie.id.in_(interacted_ids)))
    ).scalars().all()

    user_tag_ids: set[uuid.UUID] = {t.id for m in interacted for t in m.tags}
    if not user_tag_ids:
        return {mid: 0.0 for mid in movie_map}

    scores = {}
    for mid, movie in movie_map.items():
        cand_tags = {t.id for t in movie.tags}
        scores[mid] = (
            min(len(user_tag_ids & cand_tags) / len(cand_tags), 1.0)
            if cand_tags else 0.0
        )
    return scores


async def _avg_ratings(db: AsyncSession, movie_ids: List[uuid.UUID]) -> dict:
    rows = (
        await db.execute(
            select(Review.movie_id, func.avg(Review.rating).label("avg"))
            .where(Review.movie_id.in_(movie_ids))
            .group_by(Review.movie_id)
        )
    ).all()
    return {r[0]: round(float(r[1]), 2) for r in rows}
