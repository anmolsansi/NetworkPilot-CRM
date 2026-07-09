import asyncio
import errno
import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Import all models here so Alembic can detect them.
import app.models  # noqa: F401
from app.core.config import settings as app_settings
from app.db.base import Base
from app.db.database_url import asyncpg_connect_args, normalize_asyncpg_url

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)

config = context.config
database_url = normalize_asyncpg_url(app_settings.DATABASE_URL)
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

NETWORK_UNREACHABLE_MESSAGE = (
    "Database network is unreachable. If DATABASE_URL uses a Supabase direct "
    "host such as db.[project-id].supabase.co, Render may be unable to reach "
    "it over IPv6. Use the Supabase Shared Pooler session-mode URL instead: "
    "postgres://postgres.[project-ref]:[PASSWORD]@aws-[REGION].pooler.supabase.com:"
    "5432/postgres?sslmode=require, or enable the Supabase IPv4 add-on."
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = create_async_engine(
        database_url,
        poolclass=pool.NullPool,
        connect_args=asyncpg_connect_args(app_settings.DATABASE_URL),
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    except OSError as exc:
        if exc.errno == errno.ENETUNREACH:
            raise RuntimeError(NETWORK_UNREACHABLE_MESSAGE) from exc
        raise
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
