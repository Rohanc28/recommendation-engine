"""Singleton embedding service with optional in-memory caching for demo mode."""
from __future__ import annotations
import logging
from functools import lru_cache
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
        self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded")

    def encode(self, texts: List[str]) -> np.ndarray:
        """Return L2-normalised embeddings (shape N×DIM). Dot-product == cosine similarity."""
        return self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def encode_movie(self, title: str, description: str | None, tags: List[str]) -> List[float]:
        """Build a combined movie text and return its embedding as a plain list."""
        parts = [title]
        if description:
            parts.append(description)
        if tags:
            parts.append(" ".join(tags))
        vec: np.ndarray = self.encode([". ".join(parts)])[0]
        return vec.tolist()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
