"""Content pipeline: analysis, summarization, generation, moderation, publishing."""

import hashlib
import logging
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    AIAnalysis,
    AISummary,
    Analytics,
    Community,
    CommunityBlockedTopic,
    CommunityTag,
    GeneratedPost,
    JobStatus,
    ModerationResult,
    PostSource,
    PostStatus,
    PostType,
    PublishingJob,
    SourceArticle,
)
from app.services.ai.provider import get_ai_provider
from app.services.sources.collector import SourceCollector

logger = logging.getLogger(__name__)

POST_TYPE_SCHEDULE = {
    8: PostType.MORNING_UPDATE,
    11: PostType.NEWS_DISCUSSION,
    14: PostType.POLL,
    18: PostType.NEWS_DISCUSSION,
    21: PostType.EVENING_RECAP,
}

ALL_POST_TYPES = list(PostType)


class ContentPipeline:
    def __init__(self, session: AsyncSession, provider_name: str | None = None):
        self.session = session
        self.ai = get_ai_provider(provider_name)
        self.collector = SourceCollector(session)

    async def _community_to_dict(self, community: Community) -> dict:
        tags = [t.tag for t in community.tags]
        blocked = [b.topic for b in community.blocked_topics]
        return {
            "id": str(community.id),
            "name": community.name,
            "description": community.description,
            "category": community.category,
            "tags": tags,
            "blocked_topics": blocked,
            "language": community.language,
            "country": community.country,
            "region": community.region,
            "preferred_tone": community.preferred_tone,
            "is_child_safe": community.is_child_safe,
        }

    async def _get_community(self, community_id: UUID) -> Community | None:
        result = await self.session.execute(
            select(Community)
            .options(selectinload(Community.tags), selectinload(Community.blocked_topics))
            .where(Community.id == community_id)
        )
        return result.scalar_one_or_none()

    async def _get_relevant_article(self, community: Community) -> SourceArticle | None:
        blocked = {b.topic.lower() for b in community.blocked_topics}
        category = community.category.lower()

        result = await self.session.execute(
            select(SourceArticle)
            .where(SourceArticle.is_processed == False)  # noqa: E712
            .order_by(SourceArticle.collected_at.desc())
            .limit(50)
        )
        articles = result.scalars().all()

        for article in articles:
            topic = (article.topic or article.category or "").lower()
            if any(b in topic for b in blocked):
                continue
            if category in ("football", "cricket", "sports") and topic and category not in topic:
                if not any(t in topic for t in [tag.tag.lower() for tag in community.tags]):
                    continue
            return article

        if articles:
            return articles[0]
        return None

    async def _pick_post_type(self, community_id: UUID) -> PostType:
        hour = datetime.now(timezone.utc).hour
        base_type = POST_TYPE_SCHEDULE.get(hour, PostType.COMMUNITY_QUESTION)

        recent = await self.session.execute(
            select(GeneratedPost.post_type)
            .where(
                GeneratedPost.community_id == community_id,
                GeneratedPost.created_at >= datetime.now(timezone.utc) - timedelta(hours=24),
            )
            .limit(10)
        )
        recent_types = {r[0] for r in recent.all()}

        candidates = [t for t in ALL_POST_TYPES if t not in recent_types]
        if not candidates:
            candidates = ALL_POST_TYPES

        if random.random() < 0.6:
            return base_type
        return random.choice(candidates)

    async def process_article(self, article: SourceArticle, community_ctx: dict) -> tuple[AIAnalysis, AISummary]:
        article_dict = {
            "title": article.title,
            "source_name": article.source_name,
            "source_url": article.source_url,
            "content": article.raw_content or article.title,
        }

        analysis_result = await self.ai.analyze_content(
            article.title, article.raw_content or article.title, community_ctx
        )
        summary_result = await self.ai.summarize(article.title, article.raw_content or article.title)

        analysis = AIAnalysis(
            article_id=article.id,
            topic=analysis_result.topic,
            entities=analysis_result.entities,
            people=analysis_result.people,
            locations=analysis_result.locations,
            organizations=analysis_result.organizations,
            sentiment=analysis_result.sentiment,
            keywords=analysis_result.keywords,
            relevance_score=Decimal(str(analysis_result.relevance_score)),
            community_match_scores={community_ctx["id"]: analysis_result.relevance_score},
            provider=self.ai.name,
            model=self.ai.model,
        )
        summary = AISummary(
            article_id=article.id,
            short_summary=summary_result.short_summary,
            medium_summary=summary_result.medium_summary,
            long_summary=summary_result.long_summary,
            provider=self.ai.name,
            model=self.ai.model,
        )

        self.session.add(analysis)
        self.session.add(summary)
        article.is_processed = True
        await self.session.flush()
        return analysis, summary

    async def generate_post(
        self,
        community_id: UUID,
        post_type: PostType | None = None,
        article_id: UUID | None = None,
    ) -> GeneratedPost | None:
        community = await self._get_community(community_id)
        if not community or not community.is_active:
            return None

        # Capture community data before async AI calls expire the ORM session
        community_ctx = await self._community_to_dict(community)
        community_id_val = community.id
        is_child_safe = community.is_child_safe

        # Fetch latest articles from this community's linked sources
        await self.collector.collect_for_community(community_id_val)

        if article_id:
            result = await self.session.execute(
                select(SourceArticle).where(SourceArticle.id == article_id)
            )
            article = result.scalar_one_or_none()
        else:
            article = await self._get_relevant_article(community)

        if not article:
            article = await self._create_fallback_article(community)

        analysis, summary = await self.process_article(article, community_ctx)
        chosen_type = post_type or await self._pick_post_type(community_id_val)

        article_dict = {
            "title": article.title,
            "source_name": article.source_name,
            "source_url": article.source_url,
        }

        from app.services.ai.provider import AnalysisResult, SummaryResult

        ar = AnalysisResult(
            topic=analysis.topic or community_ctx["category"],
            entities=analysis.entities or [],
            people=analysis.people or [],
            locations=analysis.locations or [],
            organizations=analysis.organizations or [],
            sentiment=analysis.sentiment or "neutral",
            keywords=analysis.keywords or [],
            relevance_score=float(analysis.relevance_score or 0.8),
        )
        sr = SummaryResult(
            short_summary=summary.short_summary or article.title,
            medium_summary=summary.medium_summary or article.title,
            long_summary=summary.long_summary or article.title,
        )

        generated = await self.ai.generate_post(community_ctx, article_dict, ar, sr, chosen_type.value)

        body = generated.body
        if "Sources:" not in body and "source" not in body.lower():
            body += f"\n\nSources:\n- {article.source_name}"

        post = GeneratedPost(
            community_id=community_id_val,
            article_id=article.id,
            title=generated.title,
            body=body,
            post_type=PostType(generated.post_type) if generated.post_type in [t.value for t in PostType] else chosen_type,
            tone=generated.tone,
            hashtags=generated.hashtags,
            poll_options=generated.poll_options,
            status=PostStatus.PENDING_MODERATION,
            provider=self.ai.name,
            model=self.ai.model,
            scheduled_at=datetime.now(timezone.utc),
        )
        self.session.add(post)
        await self.session.flush()

        self.session.add(
            PostSource(
                post_id=post.id,
                source_name=article.source_name,
                source_url=article.source_url,
                article_id=article.id,
            )
        )

        await self.moderate_and_publish(post, is_child_safe)
        await self._update_analytics(community_id_val, post)
        await self.session.refresh(post)
        return post

    async def _create_fallback_article(self, community: Community) -> SourceArticle:
        from app.models import Source

        result = await self.session.execute(select(Source).where(Source.is_active == True).limit(1))  # noqa: E712
        source = result.scalar_one_or_none()
        if not source:
            raise ValueError("No active sources configured")

        article = SourceArticle(
            source_id=source.id,
            source_name="Kawn Community Engine",
            source_url="https://kawn.app",
            title=f"Community update for {community.name}",
            category=community.category,
            topic=community.category,
            raw_content=f"Latest discussions and updates for the {community.name} community. "
            f"Category: {community.category}. Join the conversation!",
            content_hash=hashlib.sha256(
                f"fallback-{community.id}-{datetime.now(timezone.utc).timestamp()}".encode()
            ).hexdigest(),
        )
        self.session.add(article)
        await self.session.flush()
        return article

    async def moderate_and_publish(self, post: GeneratedPost, is_child_safe: bool = False) -> bool:
        mod_result = await self.ai.moderate(post.title, post.body, is_child_safe)

        moderation = ModerationResult(
            post_id=post.id,
            is_safe=mod_result.is_safe,
            overall_score=Decimal(str(mod_result.overall_score)),
            checks=mod_result.checks,
            flags=mod_result.flags,
            reason=mod_result.reason,
            provider=self.ai.name,
            model=self.ai.model,
        )
        self.session.add(moderation)

        if mod_result.is_safe:
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.now(timezone.utc)
            return True

        post.status = PostStatus.BLOCKED
        return False

    async def block_post(self, post_id: UUID, reason: str | None = None) -> GeneratedPost | None:
        result = await self.session.execute(select(GeneratedPost).where(GeneratedPost.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            return None
        post.status = PostStatus.BLOCKED
        moderation = ModerationResult(
            post_id=post.id,
            is_safe=False,
            overall_score=Decimal("0.0"),
            checks={"manual_block": False},
            flags=["manual_block"],
            reason=reason or "Manually blocked by admin",
            provider="admin",
            model="manual",
        )
        self.session.add(moderation)
        await self.session.flush()
        return post

    async def publish_posts(self, post_ids: list[UUID] | None = None, community_id: UUID | None = None) -> int:
        query = select(GeneratedPost).where(GeneratedPost.status == PostStatus.APPROVED)
        if post_ids:
            query = query.where(GeneratedPost.id.in_(post_ids))
        if community_id:
            query = query.where(GeneratedPost.community_id == community_id)

        result = await self.session.execute(query)
        posts = result.scalars().all()
        count = 0
        for post in posts:
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.now(timezone.utc)
            count += 1
        await self.session.flush()
        return count

    async def _update_analytics(self, community_id: UUID, post: GeneratedPost) -> None:
        today = date.today()
        result = await self.session.execute(
            select(Analytics).where(
                Analytics.community_id == community_id,
                Analytics.metric_date == today,
            )
        )
        analytics = result.scalar_one_or_none()
        if not analytics:
            analytics = Analytics(
                community_id=community_id,
                metric_date=today,
                posts_generated=0,
                posts_published=0,
                posts_blocked=0,
                posts_failed=0,
            )
            self.session.add(analytics)

        analytics.posts_generated = (analytics.posts_generated or 0) + 1
        if post.status == PostStatus.PUBLISHED:
            analytics.posts_published = (analytics.posts_published or 0) + 1
        elif post.status == PostStatus.BLOCKED:
            analytics.posts_blocked = (analytics.posts_blocked or 0) + 1
        elif post.status == PostStatus.FAILED:
            analytics.posts_failed = (analytics.posts_failed or 0) + 1

        breakdown = dict(analytics.post_type_breakdown or {})
        pt = post.post_type.value
        breakdown[pt] = breakdown.get(pt, 0) + 1
        analytics.post_type_breakdown = breakdown
        await self.session.flush()

    async def run_community_pipeline(self, community_id: UUID, posts_count: int = 1) -> PublishingJob:
        job = PublishingJob(
            community_id=community_id,
            job_type="community_pipeline",
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(job)
        await self.session.flush()

        try:
            articles = await self.collector.collect_for_community(community_id)
            job.articles_collected = articles

            for _ in range(posts_count):
                post = await self.generate_post(community_id)
                if post:
                    job.posts_generated += 1
                    if post.status == PostStatus.PUBLISHED:
                        job.posts_published += 1
                    elif post.status == PostStatus.BLOCKED:
                        job.posts_blocked += 1
                    else:
                        job.posts_failed += 1

            job.status = JobStatus.COMPLETED
        except Exception as e:
            logger.exception("Pipeline failed for community %s", community_id)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
        finally:
            job.completed_at = datetime.now(timezone.utc)

        await self.session.flush()
        return job

    async def run_full_pipeline(self) -> list[PublishingJob]:
        result = await self.session.execute(
            select(Community).where(Community.is_active == True)  # noqa: E712
        )
        communities = result.scalars().all()
        jobs = []

        await self.collector.collect_all()

        for community in communities:
            job = await self.run_community_pipeline(community.id, posts_count=1)
            jobs.append(job)

        return jobs
