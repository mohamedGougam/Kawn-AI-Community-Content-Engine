"""Database connection and session management."""

from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


def _normalize_async_url(url: str) -> tuple[str, dict]:
    """Ensure asyncpg URL and SSL connect_args for Render Postgres."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    connect_args: dict = {}

    ssl_required = (
        "render.com" in (parsed.hostname or "")
        or query.get("sslmode", [""])[0] in ("require", "verify-full", "verify-ca")
    )
    if ssl_required:
        connect_args["ssl"] = True

    query.pop("sslmode", None)
    clean = parsed._replace(query=urlencode({k: v[0] for k, v in query.items()}))
    return urlunparse(clean), connect_args


_db_url, _connect_args = _normalize_async_url(settings.database_url)

engine = create_async_engine(
    _db_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
