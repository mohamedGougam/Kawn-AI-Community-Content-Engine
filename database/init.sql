-- Kawn AI Community Content Engine - PostgreSQL Schema
-- Version 1.0

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- COMMUNITIES
-- ============================================================
CREATE TABLE communities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    country VARCHAR(100),
    region VARCHAR(100),
    preferred_tone VARCHAR(50) DEFAULT 'friendly',
    posts_per_day INTEGER DEFAULT 5,
    publishing_frequency VARCHAR(20) DEFAULT 'daily',
    is_active BOOLEAN DEFAULT TRUE,
    is_child_safe BOOLEAN DEFAULT FALSE,
    kawn_community_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE community_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    UNIQUE(community_id, tag)
);

CREATE TABLE community_blocked_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    UNIQUE(community_id, topic)
);

-- ============================================================
-- SOURCES
-- ============================================================
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- rss, news_api, sports_api, public_api, website
    url TEXT NOT NULL,
    api_key_env VARCHAR(100),
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    reliability_score DECIMAL(3,2) DEFAULT 0.80,
    fetch_interval_minutes INTEGER DEFAULT 60,
    last_fetched_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE community_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 1,
    UNIQUE(community_id, source_id)
);

-- ============================================================
-- SOURCE ARTICLES
-- ============================================================
CREATE TABLE source_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    source_name VARCHAR(255) NOT NULL,
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    author VARCHAR(255),
    publication_date TIMESTAMPTZ,
    category VARCHAR(100),
    topic VARCHAR(255),
    raw_content TEXT,
    content_hash VARCHAR(64) UNIQUE,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    is_processed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_source_articles_source_id ON source_articles(source_id);
CREATE INDEX idx_source_articles_topic ON source_articles(topic);
CREATE INDEX idx_source_articles_collected_at ON source_articles(collected_at DESC);

-- ============================================================
-- AI ANALYSIS
-- ============================================================
CREATE TABLE ai_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES source_articles(id) ON DELETE CASCADE,
    topic VARCHAR(255),
    entities JSONB DEFAULT '[]',
    people JSONB DEFAULT '[]',
    locations JSONB DEFAULT '[]',
    organizations JSONB DEFAULT '[]',
    sentiment VARCHAR(20),
    keywords JSONB DEFAULT '[]',
    relevance_score DECIMAL(3,2),
    community_match_scores JSONB DEFAULT '{}',
    provider VARCHAR(50),
    model VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_analysis_article_id ON ai_analysis(article_id);

-- ============================================================
-- AI SUMMARIES
-- ============================================================
CREATE TABLE ai_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES source_articles(id) ON DELETE CASCADE,
    short_summary TEXT,   -- max 50 words
    medium_summary TEXT,  -- max 150 words
    long_summary TEXT,    -- max 300 words
    provider VARCHAR(50),
    model VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- GENERATED POSTS
-- ============================================================
CREATE TYPE post_type AS ENUM (
    'news_discussion',
    'poll',
    'match_prediction',
    'community_question',
    'fun_fact',
    'weekly_digest',
    'morning_update',
    'evening_recap'
);

CREATE TYPE post_status AS ENUM (
    'draft',
    'pending_moderation',
    'approved',
    'published',
    'blocked',
    'failed'
);

CREATE TABLE generated_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    article_id UUID REFERENCES source_articles(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    post_type post_type NOT NULL,
    tone VARCHAR(50) DEFAULT 'friendly',
    hashtags JSONB DEFAULT '[]',
    poll_options JSONB,
    status post_status DEFAULT 'draft',
    scheduled_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    kawn_post_id VARCHAR(100),
    provider VARCHAR(50),
    model VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_generated_posts_community_id ON generated_posts(community_id);
CREATE INDEX idx_generated_posts_status ON generated_posts(status);
CREATE INDEX idx_generated_posts_created_at ON generated_posts(created_at DESC);

-- ============================================================
-- POST SOURCES (Attribution)
-- ============================================================
CREATE TABLE post_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES generated_posts(id) ON DELETE CASCADE,
    source_name VARCHAR(255) NOT NULL,
    source_url TEXT,
    article_id UUID REFERENCES source_articles(id) ON DELETE SET NULL
);

-- ============================================================
-- MODERATION
-- ============================================================
CREATE TABLE moderation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES generated_posts(id) ON DELETE CASCADE,
    is_safe BOOLEAN NOT NULL,
    overall_score DECIMAL(3,2),
    checks JSONB DEFAULT '{}',
    flags JSONB DEFAULT '[]',
    reason TEXT,
    provider VARCHAR(50),
    model VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_moderation_results_post_id ON moderation_results(post_id);

-- ============================================================
-- PUBLISHING JOBS
-- ============================================================
CREATE TYPE job_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'partial'
);

CREATE TABLE publishing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_id UUID REFERENCES communities(id) ON DELETE SET NULL,
    job_type VARCHAR(50) NOT NULL,
    status job_status DEFAULT 'pending',
    posts_generated INTEGER DEFAULT 0,
    posts_published INTEGER DEFAULT 0,
    posts_blocked INTEGER DEFAULT 0,
    posts_failed INTEGER DEFAULT 0,
    articles_collected INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_publishing_jobs_status ON publishing_jobs(status);
CREATE INDEX idx_publishing_jobs_created_at ON publishing_jobs(created_at DESC);

-- ============================================================
-- ANALYTICS
-- ============================================================
CREATE TABLE analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_id UUID REFERENCES communities(id) ON DELETE SET NULL,
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    posts_generated INTEGER DEFAULT 0,
    posts_published INTEGER DEFAULT 0,
    posts_blocked INTEGER DEFAULT 0,
    posts_failed INTEGER DEFAULT 0,
    sources_used INTEGER DEFAULT 0,
    articles_collected INTEGER DEFAULT 0,
    engagement_score DECIMAL(5,2) DEFAULT 0,
    post_type_breakdown JSONB DEFAULT '{}',
    topic_breakdown JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(community_id, metric_date)
);

CREATE INDEX idx_analytics_metric_date ON analytics(metric_date DESC);

-- ============================================================
-- AI PROVIDER SETTINGS
-- ============================================================
CREATE TABLE ai_provider_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE,
    model VARCHAR(100),
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2048,
    api_key_env VARCHAR(100),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- PROMPT TEMPLATES
-- ============================================================
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    template TEXT NOT NULL,
    post_type post_type,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_communities_updated_at BEFORE UPDATE ON communities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_generated_posts_updated_at BEFORE UPDATE ON generated_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_provider_settings_updated_at BEFORE UPDATE ON ai_provider_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
