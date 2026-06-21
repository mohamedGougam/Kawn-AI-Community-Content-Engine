"""Initialize PostgreSQL schema on first startup (Render/production)."""

import logging
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import asyncpg

from app.config import get_settings

logger = logging.getLogger(__name__)

INIT_SQL_PATH = Path(__file__).resolve().parent.parent / "database" / "init.sql"

SCHEMA_MIGRATIONS = """
ALTER TABLE communities ADD COLUMN IF NOT EXISTS kawn_community_id VARCHAR(100);
ALTER TABLE generated_posts ADD COLUMN IF NOT EXISTS kawn_post_id VARCHAR(100);

UPDATE generated_posts
SET status = 'approved', published_at = NULL
WHERE status = 'published' AND kawn_post_id IS NULL;

UPDATE analytics SET posts_published = 0;
"""


def _asyncpg_dsn(database_url: str) -> tuple[str, bool]:
    """Convert SQLAlchemy URL to asyncpg DSN and detect SSL requirement."""
    url = database_url
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    ssl_required = (
        "render.com" in (parsed.hostname or "")
        or query.get("sslmode", [""])[0] in ("require", "verify-full", "verify-ca")
    )
    # asyncpg uses its own ssl param; strip sslmode from DSN
    query.pop("sslmode", None)
    clean = parsed._replace(query=urlencode({k: v[0] for k, v in query.items()}))
    return urlunparse(clean), ssl_required


async def ensure_database_schema() -> None:
    settings = get_settings()
    dsn, ssl_required = _asyncpg_dsn(settings.database_url)
    use_ssl = ssl_required or ("render.com" in dsn)

    try:
        conn = await asyncpg.connect(dsn, ssl=use_ssl)
    except Exception as e:
        logger.error("Database connection failed during init: %s", e)
        raise

    try:
        exists = await conn.fetchval("SELECT to_regclass('public.communities')")
        if not exists:
            if not INIT_SQL_PATH.exists():
                logger.error("init.sql not found at %s", INIT_SQL_PATH)
                raise FileNotFoundError(f"Missing schema file: {INIT_SQL_PATH}")

            logger.info("Initializing database schema from init.sql...")
            await conn.execute(INIT_SQL_PATH.read_text(encoding="utf-8"))
            logger.info("Database schema initialized successfully.")
        else:
            logger.info("Applying schema migrations...")
            await conn.execute(SCHEMA_MIGRATIONS)
            logger.info("Schema migrations applied.")
    finally:
        await conn.close()
