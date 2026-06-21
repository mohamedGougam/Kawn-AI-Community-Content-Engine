"""Analytics API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Analytics, Community, GeneratedPost, PostStatus, Source
from app.schemas import AnalyticsOverview, CommunityAnalytics
from app.services.ai.provider import get_ai_provider, provider_has_key, PROVIDERS

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsOverview)
async def get_analytics_overview(db: AsyncSession = Depends(get_db)):
    total_communities = (await db.execute(select(func.count(Community.id)))).scalar() or 0
    active_communities = (
        await db.execute(select(func.count(Community.id)).where(Community.is_active == True))  # noqa: E712
    ).scalar() or 0

    total_generated = (await db.execute(select(func.count(GeneratedPost.id)))).scalar() or 0
    total_approved = (
        await db.execute(
            select(func.count(GeneratedPost.id)).where(GeneratedPost.status == PostStatus.APPROVED)
        )
    ).scalar() or 0
    total_published = (
        await db.execute(
            select(func.count(GeneratedPost.id)).where(GeneratedPost.kawn_post_id.isnot(None))
        )
    ).scalar() or 0
    total_blocked = (
        await db.execute(
            select(func.count(GeneratedPost.id)).where(GeneratedPost.status == PostStatus.BLOCKED)
        )
    ).scalar() or 0
    total_failed = (
        await db.execute(
            select(func.count(GeneratedPost.id)).where(GeneratedPost.status == PostStatus.FAILED)
        )
    ).scalar() or 0
    active_sources = (
        await db.execute(select(func.count(Source.id)).where(Source.is_active == True))  # noqa: E712
    ).scalar() or 0

    ai_status = {}
    for name in PROVIDERS:
        ai_status[name] = {
            "available": True,
            "has_api_key": provider_has_key(name),
            "active": name == get_ai_provider().name,
        }

    post_types = await db.execute(
        select(GeneratedPost.post_type, func.count(GeneratedPost.id)).group_by(GeneratedPost.post_type)
    )
    post_type_breakdown = {str(pt.value): count for pt, count in post_types.all()}

    top = await db.execute(
        select(Community.name, func.count(GeneratedPost.id).label("count"))
        .join(GeneratedPost, GeneratedPost.community_id == Community.id)
        .group_by(Community.name)
        .order_by(func.count(GeneratedPost.id).desc())
        .limit(5)
    )
    top_communities = [{"name": name, "posts": count} for name, count in top.all()]

    recent = await db.execute(
        select(GeneratedPost.title, GeneratedPost.status, GeneratedPost.created_at, Community.name)
        .join(Community, Community.id == GeneratedPost.community_id)
        .order_by(GeneratedPost.created_at.desc())
        .limit(10)
    )
    recent_activity = [
        {"title": t, "status": s.value, "created_at": c.isoformat(), "community": n}
        for t, s, c, n in recent.all()
    ]

    return AnalyticsOverview(
        total_communities=total_communities,
        active_communities=active_communities,
        total_generated_posts=total_generated,
        total_approved_posts=total_approved,
        total_published_posts=total_published,
        total_blocked_posts=total_blocked,
        total_failed_posts=total_failed,
        active_sources=active_sources,
        ai_provider_status=ai_status,
        post_type_breakdown=post_type_breakdown,
        top_communities=top_communities,
        recent_activity=recent_activity,
    )


@router.get("/community/{community_id}", response_model=CommunityAnalytics)
async def get_community_analytics(community_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Community).where(Community.id == community_id))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    analytics_result = await db.execute(
        select(Analytics)
        .where(Analytics.community_id == community_id)
        .order_by(Analytics.metric_date.desc())
        .limit(30)
    )
    daily = analytics_result.scalars().all()

    daily_metrics = [
        {
            "date": a.metric_date.isoformat(),
            "generated": a.posts_generated,
            "published": a.posts_published,
            "blocked": a.posts_blocked,
            "failed": a.posts_failed,
        }
        for a in daily
    ]

    post_type_breakdown: dict = {}
    topic_breakdown: dict = {}
    total_gen = total_pub = total_blk = 0

    for a in daily:
        total_gen += a.posts_generated
        total_pub += a.posts_published
        total_blk += a.posts_blocked
        for k, v in (a.post_type_breakdown or {}).items():
            post_type_breakdown[k] = post_type_breakdown.get(k, 0) + v
        for k, v in (a.topic_breakdown or {}).items():
            topic_breakdown[k] = topic_breakdown.get(k, 0) + v

    return CommunityAnalytics(
        community_id=community.id,
        community_name=community.name,
        daily_metrics=daily_metrics,
        post_type_breakdown=post_type_breakdown,
        topic_breakdown=topic_breakdown,
        total_generated=total_gen,
        total_published=total_pub,
        total_blocked=total_blk,
    )
