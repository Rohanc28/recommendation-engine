import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import async_engine, init_db
from app.services.embedding import get_embedding_service
from app.services.demo_cache import stats as cache_stats
from app.routers import auth, movies, reviews, recommendations, tags, votes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("DB tables ensured")

    logger.info("Warming up embedding model…")
    get_embedding_service()
    logger.info("Ready — demo_mode=%s", settings.DEMO_MODE)
    yield
    await async_engine.dispose()


app = FastAPI(
    title="Community Movie Recommendation Engine",
    version="1.0.0",
    description="Hybrid recommendation engine: embeddings + tags + user prefs + community votes",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(reviews.router)
app.include_router(recommendations.router)
app.include_router(tags.router)
app.include_router(votes.router)


@app.get("/health", tags=["infra"])
async def health():
    return {
        "status": "ok",
        "demo_mode": settings.DEMO_MODE,
        "cache": cache_stats(),
    }
