from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ASYNC_PG_SCHEME = "postgresql+asyncpg"
POSTGRES_SCHEMES = {"postgres", "postgresql"}
LIBPQ_ONLY_QUERY_PARAMS = {
    "channel_binding",
    "connection_limit",
    "pgbouncer",
    "sslcert",
    "sslcrl",
    "sslkey",
    "sslmode",
    "sslrootcert",
}
SSL_MODES = {"allow", "disable", "prefer", "require", "verify-ca", "verify-full"}


def normalize_asyncpg_url(database_url: str) -> str:
    """Return a SQLAlchemy asyncpg URL from common hosted Postgres URLs."""
    parsed = urlsplit(database_url)
    scheme = ASYNC_PG_SCHEME if parsed.scheme in POSTGRES_SCHEMES else parsed.scheme
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in LIBPQ_ONLY_QUERY_PARAMS
    ]

    return urlunsplit(
        (
            scheme,
            parsed.netloc,
            parsed.path,
            urlencode(query, doseq=True),
            parsed.fragment,
        )
    )


def asyncpg_connect_args(database_url: str) -> dict[str, str]:
    """Translate libpq SSL query parameters into asyncpg connect kwargs."""
    query = dict(parse_qsl(urlsplit(database_url).query, keep_blank_values=True))
    sslmode = query.get("sslmode", "").lower()

    if sslmode in SSL_MODES:
        return {"ssl": sslmode}

    return {}
