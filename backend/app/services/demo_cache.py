"""
In-memory caches for demo / Cloud Run free-tier deployment.

Two caches:
  - embedding_cache  : {movie_id_str -> np.ndarray}  never expires (embeddings are stable)
  - rec_cache        : {movie_id_str -> (unix_ts, results)}  expires after TTL

Both are module-level dicts (process-local). For a single-instance Cloud Run
deployment this is perfectly fine and avoids Redis / external state.
"""
from __future__ import annotations
import time
import logging
from typing import Optional
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

# ── embedding cache ───────────────────────────────────────────────────────────
_embedding_cache: dict[str, np.ndarray] = {}


def get_cached_embedding(movie_id: str) -> Optional[np.ndarray]:
    return _embedding_cache.get(movie_id)


def set_cached_embedding(movie_id: str, vec: list[float]) -> None:
    _embedding_cache[movie_id] = np.array(vec, dtype=np.float32)


def invalidate_embedding(movie_id: str) -> None:
    _embedding_cache.pop(movie_id, None)


def cache_size() -> int:
    return len(_embedding_cache)


# ── recommendation result cache ───────────────────────────────────────────────
_rec_cache: dict[str, tuple[float, list]] = {}


def get_cached_recs(movie_id: str) -> Optional[list]:
    entry = _rec_cache.get(movie_id)
    if entry is None:
        return None
    ts, results = entry
    if time.time() - ts > settings.DEMO_REC_CACHE_TTL:
        del _rec_cache[movie_id]
        return None
    logger.debug("rec cache hit for %s", movie_id)
    return results


def set_cached_recs(movie_id: str, results: list) -> None:
    _rec_cache[movie_id] = (time.time(), results)


def invalidate_recs(movie_id: str) -> None:
    """Invalidate all cached rec entries that mention this movie_id (any user)."""
    keys_to_del = [k for k in _rec_cache if k.startswith(movie_id + ":") or k == movie_id]
    for k in keys_to_del:
        del _rec_cache[k]


def clear_all() -> None:
    _embedding_cache.clear()
    _rec_cache.clear()
    logger.info("Demo caches cleared")


def stats() -> dict:
    return {
        "embedding_cache_size": len(_embedding_cache),
        "rec_cache_size": len(_rec_cache),
    }
