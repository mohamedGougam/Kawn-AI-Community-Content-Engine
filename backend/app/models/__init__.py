"""SQLAlchemy ORM models."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [e.value for e in enum_cls]


class PostType(str, enum.Enum):
    NEWS_DISCUSSION = "news_discussion"
    POLL = "poll"
    MATCH_PREDICTION = "match_prediction"
    COMMUNITY_QUESTION = "community_question"
    FUN_FACT = "fun_fact"
    WEEKLY_DIGEST = "weekly_digest"
    MORNING_UPDATE = "morning_update"
    EVENING_RECAP = "evening_recap"


class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_MODERATION = "pending_moderation"
    APPROVED = "approved"
    PUBLISHED = "published"
    BLOCKED = "blocked"
    FAILED = "failed"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    country: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    preferred_tone: Mapped[str] = mapped_column(String(50), default="friendly")
    posts_per_day: Mapped[int] = mapped_column(Integer, default=5)
    publishing_frequency: Mapped[str] = mapped_column(String(20), default="daily")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_child_safe: Mapped[bool] = mapped_column(Boolean, default=False)
    kawn_community_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tags: Mapped[list["CommunityTag"]] = relationship(back_populates="community", cascade="all, delete-orphan")
    blocked_topics: Mapped[list["CommunityBlockedTopic"]] = relationship(
        back_populates="community", cascade="all, delete-orphan"
    )
    posts: Mapped[list["GeneratedPost"]] = relationship(back_populates="community")
    analytics: Mapped[list["Analytics"]] = relationship(back_populates="community")


class CommunityTag(Base):
    __tablename__ = "community_tags"
    __table_args__ = (UniqueConstraint("community_id", "tag"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    tag: Mapped[str] = mapped_column(String(100), nullable=False)

    community: Mapped["Community"] = relationship(back_populates="tags")


class CommunityBlockedTopic(Base):
    __tablename__ = "community_blocked_topics"
    __table_args__ = (UniqueConstraint("community_id", "topic"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    topic: Mapped[str] = mapped_column(String(255), nullable=False)

    community: Mapped["Community"] = relationship(back_populates="blocked_topics")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_env: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    reliability_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.80"))
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    articles: Mapped[list["SourceArticle"]] = relationship(back_populates="source")


class CommunitySource(Base):
    __tablename__ = "community_sources"
    __table_args__ = (UniqueConstraint("community_id", "source_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    priority: Mapped[int] = mapped_column(Integer, default=1)


class SourceArticle(Base):
    __tablename__ = "source_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255))
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    category: Mapped[str | None] = mapped_column(String(100))
    topic: Mapped[str | None] = mapped_column(String(255))
    raw_content: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    source: Mapped["Source"] = relationship(back_populates="articles")
    analyses: Mapped[list["AIAnalysis"]] = relationship(back_populates="article")
    summaries: Mapped[list["AISummary"]] = relationship(back_populates="article")


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_articles.id", ondelete="CASCADE"))
    topic: Mapped[str | None] = mapped_column(String(255))
    entities: Mapped[dict] = mapped_column(JSONB, default=list)
    people: Mapped[dict] = mapped_column(JSONB, default=list)
    locations: Mapped[dict] = mapped_column(JSONB, default=list)
    organizations: Mapped[dict] = mapped_column(JSONB, default=list)
    sentiment: Mapped[str | None] = mapped_column(String(20))
    keywords: Mapped[dict] = mapped_column(JSONB, default=list)
    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    community_match_scores: Mapped[dict] = mapped_column(JSONB, default=dict)
    provider: Mapped[str | None] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    article: Mapped["SourceArticle"] = relationship(back_populates="analyses")


class AISummary(Base):
    __tablename__ = "ai_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_articles.id", ondelete="CASCADE"))
    short_summary: Mapped[str | None] = mapped_column(Text)
    medium_summary: Mapped[str | None] = mapped_column(Text)
    long_summary: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    article: Mapped["SourceArticle"] = relationship(back_populates="summaries")


class GeneratedPost(Base):
    __tablename__ = "generated_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    article_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_articles.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    post_type: Mapped[PostType] = mapped_column(
        Enum(PostType, name="post_type", create_type=False, values_callable=_enum_values)
    )
    tone: Mapped[str] = mapped_column(String(50), default="friendly")
    hashtags: Mapped[dict] = mapped_column(JSONB, default=list)
    poll_options: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus, name="post_status", create_type=False, values_callable=_enum_values),
        default=PostStatus.DRAFT,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    kawn_post_id: Mapped[str | None] = mapped_column(String(100))
    provider: Mapped[str | None] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    community: Mapped["Community"] = relationship(back_populates="posts")
    post_sources: Mapped[list["PostSource"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    moderation_results: Mapped[list["ModerationResult"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class PostSource(Base):
    __tablename__ = "post_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("generated_posts.id", ondelete="CASCADE"))
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    article_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_articles.id", ondelete="SET NULL")
    )

    post: Mapped["GeneratedPost"] = relationship(back_populates="post_sources")


class ModerationResult(Base):
    __tablename__ = "moderation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("generated_posts.id", ondelete="CASCADE"))
    is_safe: Mapped[bool] = mapped_column(Boolean, nullable=False)
    overall_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    checks: Mapped[dict] = mapped_column(JSONB, default=dict)
    flags: Mapped[dict] = mapped_column(JSONB, default=list)
    reason: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    post: Mapped["GeneratedPost"] = relationship(back_populates="moderation_results")


class PublishingJob(Base):
    __tablename__ = "publishing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("communities.id", ondelete="SET NULL")
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", create_type=False, values_callable=_enum_values),
        default=JobStatus.PENDING,
    )
    posts_generated: Mapped[int] = mapped_column(Integer, default=0)
    posts_published: Mapped[int] = mapped_column(Integer, default=0)
    posts_blocked: Mapped[int] = mapped_column(Integer, default=0)
    posts_failed: Mapped[int] = mapped_column(Integer, default=0)
    articles_collected: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Analytics(Base):
    __tablename__ = "analytics"
    __table_args__ = (UniqueConstraint("community_id", "metric_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("communities.id", ondelete="SET NULL")
    )
    metric_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    posts_generated: Mapped[int] = mapped_column(Integer, default=0)
    posts_published: Mapped[int] = mapped_column(Integer, default=0)
    posts_blocked: Mapped[int] = mapped_column(Integer, default=0)
    posts_failed: Mapped[int] = mapped_column(Integer, default=0)
    sources_used: Mapped[int] = mapped_column(Integer, default=0)
    articles_collected: Mapped[int] = mapped_column(Integer, default=0)
    engagement_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    post_type_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    topic_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    community: Mapped["Community | None"] = relationship(back_populates="analytics")


class AIProviderSetting(Base):
    __tablename__ = "ai_provider_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    model: Mapped[str | None] = mapped_column(String(100))
    temperature: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.70"))
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    api_key_env: Mapped[str | None] = mapped_column(String(100))
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
