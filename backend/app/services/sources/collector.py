"""Source ingestion framework."""

import hashlib
import logging
from datetime import datetime, timezone
from uuid import UUID

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Source, SourceArticle

logger = logging.getLogger(__name__)


class SourceCollector:
    """Collects content from RSS feeds, APIs, and trusted websites."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    async def collect_all(self) -> int:
        result = await self.session.execute(select(Source).where(Source.is_active == True))  # noqa: E712
        sources = result.scalars().all()
        total = 0
        for source in sources:
            try:
                count = await self.collect_source(source)
                total += count
                source.last_fetched_at = datetime.now(timezone.utc)
            except Exception as e:
                logger.error("Failed to collect from %s: %s", source.name, e)
        await self.session.flush()
        return total

    async def collect_source(self, source: Source) -> int:
        if source.source_type == "rss":
            return await self._collect_rss(source)
        if source.source_type == "news_api":
            return await self._collect_news_api(source)
        return await self._collect_rss(source)

    async def _collect_rss(self, source: Source) -> int:
        count = 0
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(source.url)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

        seen_hashes: set[str] = set()

        for entry in feed.entries[:20]:
            title = entry.get("title", "Untitled")
            link = entry.get("link", source.url)
            author = entry.get("author")
            pub_date = None
            if entry.get("published_parsed"):
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            content = ""
            if entry.get("summary"):
                content = entry.summary
            elif entry.get("content"):
                content = entry.content[0].get("value", "")

            content_hash = hashlib.sha256(f"{link}{title}".encode()).hexdigest()

            if content_hash in seen_hashes:
                continue

            existing = await self.session.execute(
                select(SourceArticle).where(SourceArticle.content_hash == content_hash)
            )
            if existing.scalar_one_or_none():
                continue

            seen_hashes.add(content_hash)

            article = SourceArticle(
                source_id=source.id,
                source_name=source.name,
                source_url=link,
                title=title,
                author=author,
                publication_date=pub_date,
                category=source.category,
                topic=source.category,
                raw_content=content,
                content_hash=content_hash,
            )
            try:
                async with self.session.begin_nested():
                    self.session.add(article)
                    await self.session.flush()
                count += 1
            except IntegrityError:
                logger.debug("Duplicate article skipped: %s", title)

        return count

    async def _collect_news_api(self, source: Source) -> int:
        if not self.settings.news_api_key:
            logger.warning("NEWS_API_KEY not set, skipping news API source %s", source.name)
            return 0

        count = 0
        params = {"apiKey": self.settings.news_api_key}
        if "?" in source.url:
            base_url = source.url
        else:
            base_url = source.url
            params["category"] = source.category or "general"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(base_url, params=params)
            resp.raise_for_status()
            data = resp.json()

        seen_hashes: set[str] = set()

        for item in data.get("articles", data.get("results", []))[:20]:
            title = item.get("title", "Untitled")
            link = item.get("url", item.get("link", source.url))
            content_hash = hashlib.sha256(f"{link}{title}".encode()).hexdigest()

            if content_hash in seen_hashes:
                continue

            existing = await self.session.execute(
                select(SourceArticle).where(SourceArticle.content_hash == content_hash)
            )
            if existing.scalar_one_or_none():
                continue

            seen_hashes.add(content_hash)

            pub_date = None
            if item.get("publishedAt"):
                try:
                    pub_date = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            article = SourceArticle(
                source_id=source.id,
                source_name=item.get("source", {}).get("name", source.name) if isinstance(item.get("source"), dict) else source.name,
                source_url=link,
                title=title,
                author=item.get("author"),
                publication_date=pub_date,
                category=source.category,
                topic=source.category,
                raw_content=item.get("description", item.get("content", "")),
                content_hash=content_hash,
            )
            try:
                async with self.session.begin_nested():
                    self.session.add(article)
                    await self.session.flush()
                count += 1
            except IntegrityError:
                logger.debug("Duplicate article skipped: %s", title)

        return count

    async def collect_for_community(self, community_id: UUID) -> int:
        from app.models import CommunitySource

        result = await self.session.execute(
            select(Source)
            .join(CommunitySource, CommunitySource.source_id == Source.id)
            .where(CommunitySource.community_id == community_id, Source.is_active == True)  # noqa: E712
        )
        sources = result.scalars().all()
        total = 0
        for source in sources:
            total += await self.collect_source(source)
        await self.session.flush()
        return total
