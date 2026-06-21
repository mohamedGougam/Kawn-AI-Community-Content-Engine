"""Posts API routes."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Community, GeneratedPost, ModerationResult, PostSource, PostStatus
from app.schemas import (
    PostBlockRequest,
    PostGenerateRequest,
    PostListResponse,
    PostPublishRequest,
    PostResponse,
    PostSourceRef,
    PublishingJobResponse,
)
from app.services.content_pipeline import ContentPipeline

router = APIRouter(prefix="/api/posts", tags=["posts"])
logger = logging.getLogger(__name__)


async def _post_to_response(post: GeneratedPost, db: AsyncSession) -> PostResponse:
    await db.refresh(post)
    community_name = None
    if post.community_id:
        r = await db.execute(select(Community.name).where(Community.id == post.community_id))
        community_name = r.scalar_one_or_none()

    sources_result = await db.execute(select(PostSource).where(PostSource.post_id == post.id))
    sources = [
        PostSourceRef(source_name=s.source_name, source_url=s.source_url)
        for s in sources_result.scalars().all()
    ]

    mod_result = await db.execute(
        select(ModerationResult).where(ModerationResult.post_id == post.id).order_by(ModerationResult.created_at.desc()).limit(1)
    )
    mod = mod_result.scalar_one_or_none()
    moderation = None
    if mod:
        moderation = {
            "is_safe": mod.is_safe,
            "overall_score": float(mod.overall_score) if mod.overall_score else None,
            "checks": mod.checks,
            "flags": mod.flags,
            "reason": mod.reason,
        }

    return PostResponse(
        id=post.id,
        community_id=post.community_id,
        community_name=community_name,
        article_id=post.article_id,
        title=post.title,
        body=post.body,
        post_type=post.post_type,
        tone=post.tone,
        hashtags=post.hashtags or [],
        poll_options=post.poll_options,
        status=post.status,
        kawn_post_id=post.kawn_post_id,
        sources=sources,
        moderation=moderation,
        scheduled_at=post.scheduled_at,
        published_at=post.published_at,
        provider=post.provider,
        model=post.model,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.get("", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: PostStatus | None = Query(None),
    community_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(GeneratedPost)
    count_query = select(func.count(GeneratedPost.id))

    if status:
        query = query.where(GeneratedPost.status == status)
        count_query = count_query.where(GeneratedPost.status == status)
    if community_id:
        query = query.where(GeneratedPost.community_id == community_id)
        count_query = count_query.where(GeneratedPost.community_id == community_id)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(GeneratedPost.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    posts = result.scalars().all()

    items = [await _post_to_response(p, db) for p in posts]
    return PostListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/jobs", response_model=list[PublishingJobResponse])
async def list_publishing_jobs(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    from app.models import PublishingJob

    result = await db.execute(
        select(PublishingJob).order_by(PublishingJob.created_at.desc()).limit(limit)
    )
    jobs = result.scalars().all()
    responses = []
    for job in jobs:
        community_name = None
        if job.community_id:
            r = await db.execute(select(Community.name).where(Community.id == job.community_id))
            community_name = r.scalar_one_or_none()
        responses.append(
            PublishingJobResponse(
                id=job.id,
                community_id=job.community_id,
                community_name=community_name,
                job_type=job.job_type,
                status=job.status,
                posts_generated=job.posts_generated,
                posts_published=job.posts_published,
                posts_blocked=job.posts_blocked,
                posts_failed=job.posts_failed,
                articles_collected=job.articles_collected,
                error_message=job.error_message,
                started_at=job.started_at,
                completed_at=job.completed_at,
                created_at=job.created_at,
            )
        )
    return responses


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GeneratedPost).where(GeneratedPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return await _post_to_response(post, db)


@router.post("/generate", response_model=PostResponse, status_code=201)
async def generate_post(data: PostGenerateRequest, db: AsyncSession = Depends(get_db)):
    pipeline = ContentPipeline(db)
    try:
        post = await pipeline.generate_post(data.community_id, data.post_type, data.article_id)
    except Exception as e:
        logger.exception("Post generation failed for community %s", data.community_id)
        raise HTTPException(status_code=500, detail=f"Post generation failed: {e}") from e
    if not post:
        raise HTTPException(status_code=404, detail="Community not found or inactive")
    return await _post_to_response(post, db)


@router.post("/publish")
async def publish_posts(data: PostPublishRequest, db: AsyncSession = Depends(get_db)):
    from app.services.kawn_publisher import KawnPublishError

    pipeline = ContentPipeline(db)
    try:
        count = await pipeline.publish_posts(data.post_ids or None, data.community_id)
    except KawnPublishError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return {"published_count": count}


@router.post("/block", response_model=PostResponse)
async def block_post(data: PostBlockRequest, db: AsyncSession = Depends(get_db)):
    pipeline = ContentPipeline(db)
    post = await pipeline.block_post(data.post_id, data.reason)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return await _post_to_response(post, db)
