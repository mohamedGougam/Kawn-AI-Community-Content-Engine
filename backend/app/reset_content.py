"""Clear all generated content while keeping communities and sources."""

import asyncio

from sqlalchemy import delete, func, select

from app.database import AsyncSessionLocal
from app.models import (
    AIAnalysis,
    AISummary,
    Analytics,
    GeneratedPost,
    ModerationResult,
    PostSource,
    PublishingJob,
    SourceArticle,
)


async def reset_content() -> dict:
    """Delete posts, articles, analytics, and job history. Keeps communities & sources."""
    async with AsyncSessionLocal() as session:
        counts = {}
        for label, model in [
            ("moderation_results", ModerationResult),
            ("post_sources", PostSource),
            ("generated_posts", GeneratedPost),
            ("ai_analysis", AIAnalysis),
            ("ai_summaries", AISummary),
            ("source_articles", SourceArticle),
            ("publishing_jobs", PublishingJob),
            ("analytics", Analytics),
        ]:
            n = (await session.execute(select(func.count()).select_from(model))).scalar() or 0
            counts[label] = n
            await session.execute(delete(model))

        await session.commit()

    total_posts = counts.get("generated_posts", 0)
    print(f"Reset complete: removed {total_posts} posts and related content.")
    return counts


if __name__ == "__main__":
    asyncio.run(reset_content())
