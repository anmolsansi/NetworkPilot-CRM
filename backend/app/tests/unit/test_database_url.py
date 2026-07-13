import logging

from app.db.database_url import asyncpg_connect_args, normalize_asyncpg_url

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


def test_normalizes_plain_postgresql_url_to_asyncpg() -> None:
    url = "postgresql://postgres:secret@db.example.supabase.co:5432/postgres"

    assert (
        normalize_asyncpg_url(url)
        == "postgresql+asyncpg://postgres:secret@db.example.supabase.co:5432/postgres"
    )


def test_normalizes_postgres_alias_url_to_asyncpg() -> None:
    url = "postgres://postgres:secret@db.example.supabase.co:5432/postgres"

    assert (
        normalize_asyncpg_url(url)
        == "postgresql+asyncpg://postgres:secret@db.example.supabase.co:5432/postgres"
    )


def test_removes_libpq_only_query_params_from_asyncpg_url() -> None:
    url = (
        "postgresql+asyncpg://postgres:secret@pooler.supabase.com:6543/postgres"
        "?sslmode=require&pgbouncer=true&connection_limit=1&application_name=networkpilot"
    )

    assert normalize_asyncpg_url(url) == (
        "postgresql+asyncpg://postgres:secret@pooler.supabase.com:6543/postgres"
        "?application_name=networkpilot"
    )


def test_translates_sslmode_require_to_asyncpg_ssl_arg() -> None:
    url = "postgresql://postgres:secret@db.example.supabase.co:5432/postgres?sslmode=require"

    assert asyncpg_connect_args(url) == {"ssl": "require"}


def test_translates_sslmode_disable_to_asyncpg_ssl_arg() -> None:
    url = "postgresql://postgres:secret@localhost:5432/postgres?sslmode=disable"

    assert asyncpg_connect_args(url) == {"ssl": "disable"}
