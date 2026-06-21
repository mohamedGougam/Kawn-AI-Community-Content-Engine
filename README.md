# Kawn AI Community Content Engine

An AI-powered content generation engine that automatically creates and publishes daily community posts for Kawn. Built as a standalone web application with REST APIs designed for future Flutter integration.

## Project Overview

The Kawn AI Community Content Engine solves the empty-community problem by continuously generating relevant, engaging content for thousands of topic-agnostic communities.

**Content Pipeline:**

```
Sources → AI Understanding → AI Summarization → Community Post Generation → Safety Validation → Auto Publish → Community Feed
```

## Architecture

```mermaid
flowchart TB
    subgraph Sources
        RSS[RSS Feeds]
        NewsAPI[News APIs]
        SportsAPI[Sports APIs]
        PublicAPI[Public APIs]
    end

    subgraph Backend["FastAPI Backend"]
        Collector[Source Collector]
        AIEngine[AI Engine]
        Pipeline[Content Pipeline]
        Moderation[Safety Layer]
        Scheduler[APScheduler]
        REST[REST APIs]
    end

    subgraph AIProviders["AI Providers"]
        Mock[Mock Provider]
        OpenAI[OpenAI]
        Anthropic[Anthropic]
        Gemini[Google Gemini]
        HF[Hugging Face]
    end

    subgraph Storage
        PG[(PostgreSQL)]
    end

    subgraph Frontend["Next.js Admin Portal"]
        Dashboard[Dashboard]
        Communities[Communities]
        SourcesMgmt[Sources]
        Posts[Generated Posts]
        Analytics[Analytics]
        Settings[AI Config]
    end

    RSS --> Collector
    NewsAPI --> Collector
    SportsAPI --> Collector
    PublicAPI --> Collector

    Collector --> PG
    Scheduler --> Collector
    Scheduler --> Pipeline

    Pipeline --> AIEngine
    AIEngine --> Mock
    AIEngine --> OpenAI
    AIEngine --> Anthropic
    AIEngine --> Gemini
    AIEngine --> HF

    AIEngine --> Moderation
    Moderation --> PG
    Pipeline --> PG

    REST --> PG
    Frontend --> REST
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, APScheduler |
| Frontend | Next.js 14, TypeScript, TailwindCSS, Recharts |
| Database | PostgreSQL 16 |
| AI | OpenAI, Anthropic, Gemini, Hugging Face, Mock |
| Infrastructure | Docker, Docker Compose |

## Project Structure

```
Kawn AI Community Content Engine/
├── backend/
│   ├── app/
│   │   ├── api/              # REST API routes
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/
│   │   │   ├── ai/           # AI provider abstraction
│   │   │   └── sources/      # Source ingestion
│   │   ├── scheduler/        # APScheduler jobs
│   │   ├── content_pipeline.py
│   │   ├── seed.py           # Seed data
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/
│   │   └── lib/api.ts
│   ├── package.json
│   └── Dockerfile
├── database/
│   └── init.sql              # PostgreSQL schema
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start with Docker

```bash
# 1. Clone/navigate to project
cd "C:\Kawn AI Community Content Engine"

# 2. Copy environment file
copy .env.example .env

# 3. Start all services
docker compose up --build
```

**Access:**
- Admin Portal: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

> **Tip:** Clone the repo once and run Docker from that folder only. If you see `container name "/kawn-content-db" is already in use`, run `docker compose down` first, or stop old containers: `docker stop kawn-content-db kawn-content-backend kawn-content-frontend`.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Port 5432 in use | Docker maps PostgreSQL to host port **5433** (see `docker-compose.yml`) |
| Container name conflict | `docker compose down` then `docker compose up -d --build` |
| Empty posts after generate | Restart backend after `.env` changes: `docker compose restart backend` |
| Mock/sample posts on first run | Set `SEED_SAMPLE_DATA=false` in `.env` (default) |
| Clear all posts | `POST /api/admin/reset-content` or **Generated Posts → Clear all posts** |
| Community source mapping | `GET /api/sources/mapping` or **Sources** page |

## Local Development (Without Docker)

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16

### Database Setup

```bash
# Create database
psql -U postgres -c "CREATE USER kawn WITH PASSWORD 'kawn_secret';"
psql -U postgres -c "CREATE DATABASE kawn_content_engine OWNER kawn;"
psql -U kawn -d kawn_content_engine -f database/init.sql
```

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Set environment variables (or copy .env to backend/)
set DATABASE_URL=postgresql+asyncpg://kawn:kawn_secret@localhost:5432/kawn_content_engine

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Async PostgreSQL connection | `postgresql+asyncpg://kawn:kawn_secret@localhost:5432/kawn_content_engine` |
| `AI_DEFAULT_PROVIDER` | Default AI provider | `mock` |
| `OPENAI_API_KEY` | OpenAI API key | (empty) |
| `ANTHROPIC_API_KEY` | Anthropic API key | (empty) |
| `GOOGLE_API_KEY` | Google Gemini API key | (empty) |
| `HUGGINGFACE_API_KEY` | Hugging Face API key | (empty) |
| `NEWS_API_KEY` | News API key | (empty) |
| `SCHEDULER_ENABLED` | Enable background scheduler | `true` |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend | `http://localhost:8000` |

> **Note:** Without API keys, the mock AI provider is used automatically. The app runs fully locally with realistic sample data.

## REST API

### Communities
```
GET    /api/communities
POST   /api/communities
GET    /api/communities/{id}
PUT    /api/communities/{id}
DELETE /api/communities/{id}
```

### Posts
```
GET    /api/posts
GET    /api/posts/{id}
POST   /api/posts/generate
POST   /api/posts/publish
POST   /api/posts/block
GET    /api/posts/jobs
```

### Sources
```
GET    /api/sources
POST   /api/sources
PUT    /api/sources/{id}
DELETE /api/sources/{id}
```

### Analytics
```
GET    /api/analytics
GET    /api/analytics/community/{id}
```

### AI Settings
```
GET    /api/settings/ai
POST   /api/settings/ai/{provider}
```

## API Examples

### Generate a Post

```bash
curl -X POST http://localhost:8000/api/posts/generate \
  -H "Content-Type: application/json" \
  -d '{"community_id": "YOUR_COMMUNITY_UUID", "post_type": "news_discussion"}'
```

### Create a Community

```bash
curl -X POST http://localhost:8000/api/communities \
  -H "Content-Type: application/json" \
  -d '{
    "name": "France National Team Fans",
    "category": "football",
    "tags": ["france", "football"],
    "blocked_topics": ["cricket"],
    "country": "France",
    "preferred_tone": "passionate"
  }'
```

### Get Analytics

```bash
curl http://localhost:8000/api/analytics
```

## Sample AI Workflow

1. **Source Collection** — Scheduler fetches RSS/API content every 30 minutes
2. **AI Understanding** — Extracts topics, entities, sentiment, relevance scores
3. **AI Summarization** — Creates short (50w), medium (150w), long (300w) summaries
4. **Post Generation** — Transforms content into community-engaging posts with questions/polls
5. **Safety Validation** — Checks for hate speech, misinformation, child safety, etc.
6. **Auto Publish** — Safe content is published automatically; blocked content appears in admin

### Example Transformation

**Source Article:**
> "France announced a new squad."

**Generated Post:**
> France has announced its latest squad ahead of the upcoming fixtures.
>
> Which player are you most excited to watch and why?
>
> Sources:
> - Reuters

## Supported Post Types

| Type | Description |
|------|-------------|
| `news_discussion` | News-based community discussions |
| `poll` | Community polls with options |
| `match_prediction` | Score/match predictions |
| `community_question` | Open engagement questions |
| `fun_fact` | Interesting facts |
| `weekly_digest` | Weekly community roundup |
| `morning_update` | Morning community updates |
| `evening_recap` | Evening recap posts |

## Seed Data

On first startup, the engine seeds:
- **11 communities** (France Fans, Brazil Fans, India Cricket, AI Enthusiasts, etc.)
- **8 RSS sources** (BBC Sport, ESPN Cricket, TechCrunch, etc.)
- **6 sample articles** with AI analysis and summaries
- **10 generated posts** across different communities and post types

## Scheduler

The APScheduler runs three jobs:

| Job | Schedule | Description |
|-----|----------|-------------|
| Source Collection | Every 30 min | Fetches new articles from active sources |
| Hourly Generation | Every hour | Generates 1 post per active community |
| Daily Pipeline | 06:00 UTC | Full pipeline with source collection |

## Admin Portal Pages

1. **Dashboard** — Overview stats, top communities, recent activity
2. **Communities** — CRUD communities, tags, blocked topics, child-safe flags
3. **Sources** — Manage RSS feeds and API sources
4. **Generated Posts** — View posts, moderation results, block posts
5. **Publishing History** — Scheduler job history
6. **Analytics** — Charts for post types, status distribution, top communities
7. **AI Configuration** — Provider selection, temperature, safety settings

## Flutter Integration

All endpoints return JSON and are designed for consumption by Flutter apps:

```dart
// Example Flutter integration
final response = await http.get(
  Uri.parse('$baseUrl/api/communities'),
  headers: {'Content-Type': 'application/json'},
);
final communities = jsonDecode(response.body);
```

## License

Proprietary — Kawn Platform
