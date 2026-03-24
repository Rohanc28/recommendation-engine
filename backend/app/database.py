from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event, text
from app.config import settings

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    # SQLite: allow sharing connection across threads in async context
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# Enable WAL mode + foreign keys for SQLite on every new connection
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(async_engine.sync_engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create all tables (used instead of Alembic for the SQLite/demo path)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
