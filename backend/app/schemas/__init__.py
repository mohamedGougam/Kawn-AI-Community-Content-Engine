"""Pydantic schemas for API request/response."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import JobStatus, PostStatus, PostType


# ── Community ──────────────────────────────────────────────────────────────

class CommunityTagSchema(BaseModel):
    tag: str


class CommunityCreate(BaseModel):
    name: str
    description: str | None = None
    category: str
    tags: list[str] = []
    blocked_topics: list[str] = []
    language: str = "en"
    country: str | None = None
    region: str | None = None
    preferred_tone: str = "friendly"
    posts_per_day: int = 5
    publishing_frequency: str = "daily"
    is_active: bool = True
    is_child_safe: bool = False
    kawn_community_id: str | None = None


class CommunityUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    blocked_topics: list[str] | None = None
    language: str | None = None
    country: str | None = None
    region: str | None = None
    preferred_tone: str | None = None
    posts_per_day: int | None = None
    publishing_frequency: str | None = None
    is_active: bool | None = None
    is_child_safe: bool | None = None
    kawn_community_id: str | None = None


class CommunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    category: str
    tags: list[str] = []
    blocked_topics: list[str] = []
    language: str
    country: str | None
    region: str | None
    preferred_tone: str
    posts_per_day: int
    publishing_frequency: str
    is_active: bool
    is_child_safe: bool
    kawn_community_id: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Source ─────────────────────────────────────────────────────────────────

class SourceCreate(BaseModel):
    name: str
    source_type: str
    url: str
    api_key_env: str | None = None
    category: str | None = None
    is_active: bool = True
    reliability_score: Decimal = Decimal("0.80")
    fetch_interval_minutes: int = 60


class SourceUpdate(BaseModel):
    name: str | None = None
    source_type: str | None = None
    url: str | None = None
    api_key_env: str | None = None
    category: str | None = None
    is_active: bool | None = None
    reliability_score: Decimal | None = None
    fetch_interval_minutes: int | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_type: str
    url: str
    api_key_env: str | None
    category: str | None
    is_active: bool
    reliability_score: Decimal
    fetch_interval_minutes: int
    last_fetched_at: datetime | None
    created_at: datetime
    updated_at: datetime


# ── Posts ──────────────────────────────────────────────────────────────────

class PostSourceRef(BaseModel):
    source_name: str
    source_url: str | None = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    community_id: UUID
    community_name: str | None = None
    article_id: UUID | None
    title: str
    body: str
    post_type: PostType
    tone: str
    hashtags: list[str] = []
    poll_options: list[str] | None = None
    status: PostStatus
    kawn_post_id: str | None = None
    sources: list[PostSourceRef] = []
    moderation: dict | None = None
    scheduled_at: datetime | None
    published_at: datetime | None
    provider: str | None
    model: str | None
    created_at: datetime
    updated_at: datetime


class PostGenerateRequest(BaseModel):
    community_id: UUID
    post_type: PostType | None = None
    article_id: UUID | None = None


class PostPublishRequest(BaseModel):
    post_ids: list[UUID] = Field(default_factory=list)
    community_id: UUID | None = None


class PostBlockRequest(BaseModel):
    post_id: UUID
    reason: str | None = None


class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
    page: int
    page_size: int


# ── Analytics ──────────────────────────────────────────────────────────────

class AnalyticsOverview(BaseModel):
    total_communities: int
    active_communities: int
    total_generated_posts: int
    total_approved_posts: int
    total_published_posts: int
    total_blocked_posts: int
    total_failed_posts: int
    active_sources: int
    ai_provider_status: dict
    post_type_breakdown: dict
    top_communities: list[dict]
    recent_activity: list[dict]


class CommunityAnalytics(BaseModel):
    community_id: UUID
    community_name: str
    daily_metrics: list[dict]
    post_type_breakdown: dict
    topic_breakdown: dict
    total_generated: int
    total_published: int
    total_blocked: int


# ── AI Settings ────────────────────────────────────────────────────────────

class AIProviderSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    is_active: bool
    is_default: bool
    model: str | None
    temperature: Decimal
    max_tokens: int
    api_key_env: str | None
    settings: dict
    has_api_key: bool = False


class AIProviderSettingUpdate(BaseModel):
    is_active: bool | None = None
    is_default: bool | None = None
    model: str | None = None
    temperature: Decimal | None = None
    max_tokens: int | None = None
    settings: dict | None = None


# ── Publishing Jobs ────────────────────────────────────────────────────────

class PublishingJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    community_id: UUID | None
    community_name: str | None = None
    job_type: str
    status: JobStatus
    posts_generated: int
    posts_published: int
    posts_blocked: int
    posts_failed: int
    articles_collected: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


# ── Health ─────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    scheduler_running: bool
    ai_provider: str
