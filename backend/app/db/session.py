from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.database_url import asyncpg_connect_args, normalize_asyncpg_url

engine = create_async_engine(
    normalize_asyncpg_url(settings.DATABASE_URL),
    echo=False,
    pool_pre_ping=True,
    connect_args=asyncpg_connect_args(settings.DATABASE_URL),
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
