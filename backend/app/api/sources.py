"""Source API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Community, CommunitySource, Source
from app.schemas import SourceCreate, SourceResponse, SourceUpdate

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("/mapping")
async def get_community_source_mapping(db: AsyncSession = Depends(get_db)):
    """Show which RSS/API sources each community fetches from."""
    result = await db.execute(
        select(Community)
        .options(selectinload(Community.tags))
        .where(Community.is_active == True)  # noqa: E712
        .order_by(Community.name)
    )
    communities = result.scalars().all()

    mapping = []
    for community in communities:
        src_result = await db.execute(
            select(Source)
            .join(CommunitySource, CommunitySource.source_id == Source.id)
            .where(CommunitySource.community_id == community.id)
            .order_by(Source.name)
        )
        sources = src_result.scalars().all()
        mapping.append({
            "community_id": str(community.id),
            "community_name": community.name,
            "category": community.category,
            "tags": [t.tag for t in community.tags],
            "sources": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "category": s.category,
                    "source_type": s.source_type,
                    "last_fetched_at": s.last_fetched_at.isoformat() if s.last_fetched_at else None,
                    "is_active": s.is_active,
                }
                for s in sources
            ],
        })
    return mapping


@router.get("", response_model=list[SourceResponse])
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).order_by(Source.name))
    return result.scalars().all()


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.post("", response_model=SourceResponse, status_code=201)
async def create_source(data: SourceCreate, db: AsyncSession = Depends(get_db)):
    source = Source(**data.model_dump())
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(source_id: UUID, data: SourceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    await db.flush()
    await db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)
