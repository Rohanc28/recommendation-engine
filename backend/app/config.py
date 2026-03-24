from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # SQLite default — swap to postgresql+asyncpg://... for production
    DATABASE_URL: str = "sqlite+aiosqlite:///./movies.db"

    SECRET_KEY: str = "change-me-in-production-min-32-chars-please!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000","https://recommendation-engine.vercel.app"]'

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # Demo mode: skips embedding recomputation on update + enables in-memory caches
    DEMO_MODE: bool = False
    # How many seconds to cache recommendation results in demo mode
    DEMO_REC_CACHE_TTL: int = 300

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
