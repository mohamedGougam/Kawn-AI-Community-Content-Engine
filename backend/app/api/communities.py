"""Community API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Community, CommunityBlockedTopic, CommunityTag
from app.schemas import CommunityCreate, CommunityResponse, CommunityUpdate

router = APIRouter(prefix="/api/communities", tags=["communities"])


def _to_response(community: Community) -> CommunityResponse:
    return CommunityResponse(
        id=community.id,
        name=community.name,
        description=community.description,
        category=community.category,
        tags=[t.tag for t in community.tags],
        blocked_topics=[b.topic for b in community.blocked_topics],
        language=community.language,
        country=community.country,
        region=community.region,
        preferred_tone=community.preferred_tone,
        posts_per_day=community.posts_per_day,
        publishing_frequency=community.publishing_frequency,
        is_active=community.is_active,
        is_child_safe=community.is_child_safe,
        created_at=community.created_at,
        updated_at=community.updated_at,
    )


@router.get("", response_model=list[CommunityResponse])
async def list_communities(
    active_only: bool = Query(False),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Community).options(
        selectinload(Community.tags), selectinload(Community.blocked_topics)
    )
    if active_only:
        query = query.where(Community.is_active == True)  # noqa: E712
    if category:
        query = query.where(Community.category == category)
    query = query.order_by(Community.name)
    result = await db.execute(query)
    return [_to_response(c) for c in result.scalars().all()]


@router.get("/{community_id}", response_model=CommunityResponse)
async def get_community(community_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Community)
        .options(selectinload(Community.tags), selectinload(Community.blocked_topics))
        .where(Community.id == community_id)
    )
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    return _to_response(community)


@router.post("", response_model=CommunityResponse, status_code=201)
async def create_community(data: CommunityCreate, db: AsyncSession = Depends(get_db)):
    community = Community(
        name=data.name,
        description=data.description,
        category=data.category,
        language=data.language,
        country=data.country,
        region=data.region,
        preferred_tone=data.preferred_tone,
        posts_per_day=data.posts_per_day,
        publishing_frequency=data.publishing_frequency,
        is_active=data.is_active,
        is_child_safe=data.is_child_safe,
    )
    db.add(community)
    await db.flush()

    for tag in data.tags:
        db.add(CommunityTag(community_id=community.id, tag=tag))
    for topic in data.blocked_topics:
        db.add(CommunityBlockedTopic(community_id=community.id, topic=topic))

    await db.flush()
    await db.refresh(community, ["tags", "blocked_topics"])
    return _to_response(community)


@router.put("/{community_id}", response_model=CommunityResponse)
async def update_community(
    community_id: UUID, data: CommunityUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Community)
        .options(selectinload(Community.tags), selectinload(Community.blocked_topics))
        .where(Community.id == community_id)
    )
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    update_data = data.model_dump(exclude_unset=True)
    tags = update_data.pop("tags", None)
    blocked = update_data.pop("blocked_topics", None)

    for key, value in update_data.items():
        setattr(community, key, value)

    if tags is not None:
        for t in community.tags:
            await db.delete(t)
        for tag in tags:
            db.add(CommunityTag(community_id=community.id, tag=tag))

    if blocked is not None:
        for b in community.blocked_topics:
            await db.delete(b)
        for topic in blocked:
            db.add(CommunityBlockedTopic(community_id=community.id, topic=topic))

    await db.flush()
    await db.refresh(community, ["tags", "blocked_topics"])
    return _to_response(community)


@router.delete("/{community_id}", status_code=204)
async def delete_community(community_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Community).where(Community.id == community_id))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    await db.delete(community)
