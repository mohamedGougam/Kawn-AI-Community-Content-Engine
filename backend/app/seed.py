"""Seed database with sample communities, sources, articles, and posts."""

import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import (
    AIAnalysis,
    AIProviderSetting,
    AISummary,
    Analytics,
    Community,
    CommunityBlockedTopic,
    CommunitySource,
    CommunityTag,
    GeneratedPost,
    ModerationResult,
    PostSource,
    PostStatus,
    PostType,
    PublishingJob,
    JobStatus,
    Source,
    SourceArticle,
)


COMMUNITIES = [
    {
        "name": "France National Team Fans",
        "description": "Everything about Les Bleus — squad news, match discussions, and fan debates.",
        "category": "football",
        "tags": ["france", "football", "national-team", "les-bleus"],
        "blocked_topics": ["cricket", "drawing"],
        "country": "France",
        "preferred_tone": "passionate",
    },
    {
        "name": "Algeria National Team Fans",
        "description": "The Fennecs community — match previews, player debates, and national pride.",
        "category": "football",
        "tags": ["algeria", "football", "fennecs", "national-team"],
        "blocked_topics": ["cricket", "drawing"],
        "country": "Algeria",
        "preferred_tone": "passionate",
    },
    {
        "name": "Brazil National Team Fans",
        "description": "Selecao fans unite — samba football, World Cup history, and player discussions.",
        "category": "football",
        "tags": ["brazil", "football", "selecao", "world-cup"],
        "blocked_topics": ["cricket", "drawing"],
        "country": "Brazil",
        "preferred_tone": "enthusiastic",
    },
    {
        "name": "India Cricket Fans",
        "description": "Cricket lovers discussing IPL, Test matches, and Indian cricket legends.",
        "category": "cricket",
        "tags": ["india", "cricket", "ipl", "test-cricket"],
        "blocked_topics": ["football", "drawing"],
        "country": "India",
        "preferred_tone": "friendly",
    },
    {
        "name": "Australia Cricket Fans",
        "description": "Baggy green supporters — Ashes, BBL, and Australian cricket culture.",
        "category": "cricket",
        "tags": ["australia", "cricket", "ashes", "bbl"],
        "blocked_topics": ["football", "drawing"],
        "country": "Australia",
        "preferred_tone": "friendly",
    },
    {
        "name": "Drawing Artists",
        "description": "A creative space for artists to share techniques, inspiration, and artwork.",
        "category": "art",
        "tags": ["drawing", "art", "sketching", "illustration"],
        "blocked_topics": ["football", "cricket", "politics"],
        "preferred_tone": "creative",
    },
    {
        "name": "Kids Drawing Club",
        "description": "A safe, fun space for young artists to learn and share their creations.",
        "category": "art",
        "tags": ["kids", "drawing", "art", "creative"],
        "blocked_topics": ["football", "cricket", "politics", "violence"],
        "preferred_tone": "playful",
        "is_child_safe": True,
    },
    {
        "name": "AI Enthusiasts",
        "description": "Discussing the latest in artificial intelligence, ML, and emerging tech.",
        "category": "technology",
        "tags": ["ai", "machine-learning", "technology", "innovation"],
        "blocked_topics": ["football", "cricket"],
        "preferred_tone": "informative",
    },
    {
        "name": "Data Science Community",
        "description": "Data scientists sharing insights, tools, and career discussions.",
        "category": "technology",
        "tags": ["data-science", "python", "analytics", "ml"],
        "blocked_topics": ["football", "cricket"],
        "preferred_tone": "professional",
    },
    {
        "name": "Entrepreneurs",
        "description": "Startup founders and business builders sharing strategies and lessons.",
        "category": "business",
        "tags": ["startup", "entrepreneurship", "business", "founders"],
        "blocked_topics": ["football", "cricket", "drawing"],
        "preferred_tone": "motivational",
    },
    {
        "name": "Amsterdam Community",
        "description": "Local news, events, and discussions for Amsterdam residents and visitors.",
        "category": "local",
        "tags": ["amsterdam", "netherlands", "local", "events"],
        "blocked_topics": ["football", "cricket"],
        "country": "Netherlands",
        "region": "Amsterdam",
        "preferred_tone": "welcoming",
    },
]

SOURCES = [
    {"name": "BBC Sport Football", "source_type": "rss", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml", "category": "football"},
    {"name": "ESPN Cricket", "source_type": "rss", "url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml", "category": "cricket"},
    {"name": "Reuters Sports", "source_type": "rss", "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best", "category": "sports"},
    {"name": "TechCrunch AI", "source_type": "rss", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "category": "technology"},
    {"name": "Dev.to Data Science", "source_type": "rss", "url": "https://dev.to/feed/tag/datascience", "category": "technology"},
    {"name": "Creative Bloq Art", "source_type": "rss", "url": "https://www.creativebloq.com/feeds/all", "category": "art"},
    {"name": "Startup News", "source_type": "rss", "url": "https://techcrunch.com/category/startups/feed/", "category": "business"},
    {"name": "Amsterdam Local News", "source_type": "rss", "url": "https://www.at5.nl/feeds/rss.xml", "category": "local"},
]

SAMPLE_ARTICLES = [
    {
        "title": "France announces latest squad ahead of international fixtures",
        "source_name": "Reuters",
        "category": "football",
        "topic": "football",
        "content": "The French Football Federation has announced its latest national team squad for upcoming international fixtures. Head coach Didier Deschamps included several surprise selections while maintaining a core of experienced players. The squad features a mix of established stars and emerging talents from Ligue 1 and top European leagues.",
    },
    {
        "title": "Brazil's Selecao prepare for Copa America campaign",
        "source_name": "ESPN",
        "category": "football",
        "topic": "football",
        "content": "Brazil's national team has begun preparations for the upcoming Copa America tournament. The coaching staff is evaluating tactical formations and player fitness ahead of the group stage matches. Fans are excited about the potential lineup featuring both veteran players and young prospects.",
    },
    {
        "title": "India clinches thrilling Test victory in final session",
        "source_name": "ESPN Cricinfo",
        "category": "cricket",
        "topic": "cricket",
        "content": "India secured a dramatic Test match victory in the final session on day five. The bowling attack delivered crucial breakthroughs while the batting lineup showed resilience under pressure. This win strengthens India's position in the World Test Championship standings.",
    },
    {
        "title": "New AI model achieves breakthrough in reasoning tasks",
        "source_name": "TechCrunch",
        "category": "technology",
        "topic": "artificial intelligence",
        "content": "Researchers have unveiled a new AI model that demonstrates significant improvements in complex reasoning tasks. The model shows enhanced capabilities in mathematical problem-solving, code generation, and multi-step logical inference. Industry experts believe this could accelerate AI adoption across enterprise applications.",
    },
    {
        "title": "10 essential drawing techniques every artist should master",
        "source_name": "Creative Bloq",
        "category": "art",
        "topic": "drawing",
        "content": "Professional artists share their top drawing techniques for beginners and intermediate creators. From shading fundamentals to perspective drawing, these skills form the foundation of visual art. Practice exercises are included to help artists develop their craft consistently.",
    },
    {
        "title": "Startup funding reaches new heights in Q1 2026",
        "source_name": "TechCrunch",
        "category": "business",
        "topic": "startups",
        "content": "Global startup funding hit record levels in the first quarter of 2026, with AI and climate tech leading investment rounds. Venture capital firms are increasingly focused on companies with strong unit economics and clear paths to profitability. Founders share insights on navigating the current funding landscape.",
    },
]

SAMPLE_POSTS = [
    {
        "community_match": "France National Team Fans",
        "title": "France has announced its latest squad — who are you most excited to watch?",
        "body": "According to Reuters, France has announced its latest national team squad for upcoming international fixtures.\n\nHead coach Didier Deschamps included several surprise selections while maintaining a core of experienced players.\n\nWhich player are you most excited to watch and why?\n\nSources:\n- Reuters",
        "post_type": PostType.NEWS_DISCUSSION,
        "status": PostStatus.PUBLISHED,
    },
    {
        "community_match": "Brazil National Team Fans",
        "title": "Predict Brazil's next match score!",
        "body": "Brazil's Selecao are preparing for their upcoming campaign with an exciting mix of veterans and young talent.\n\nWhat score do you predict for their next match? Drop your predictions below!\n\nSources:\n- ESPN",
        "post_type": PostType.MATCH_PREDICTION,
        "status": PostStatus.PUBLISHED,
    },
    {
        "community_match": "India Cricket Fans",
        "title": "Who was the MVP of India's latest Test victory?",
        "body": "India secured a dramatic Test match victory in the final session!\n\nWho do you think was the MVP of this match?\n- Batsman\n- Bowler\n- All-rounder\n\nSources:\n- ESPN Cricinfo",
        "post_type": PostType.POLL,
        "poll_options": ["Batsman", "Bowler", "All-rounder"],
        "status": PostStatus.PUBLISHED,
    },
    {
        "community_match": "AI Enthusiasts",
        "title": "New AI reasoning breakthrough — what applications excite you most?",
        "body": "According to TechCrunch, researchers have unveiled a new AI model with significant improvements in complex reasoning tasks.\n\nWhich application area excites you most — enterprise automation, scientific research, or creative tools?\n\nSources:\n- TechCrunch",
        "post_type": PostType.NEWS_DISCUSSION,
        "status": PostStatus.PUBLISHED,
    },
    {
        "community_match": "Drawing Artists",
        "title": "Weekly Drawing Challenge: Master Shading Techniques",
        "body": "This week's creative challenge focuses on shading fundamentals!\n\nPick an everyday object and practice creating depth with light and shadow. Share your work with the community!\n\nSources:\n- Creative Bloq",
        "post_type": PostType.COMMUNITY_QUESTION,
        "status": PostStatus.PUBLISHED,
    },
    {
        "community_match": "Kids Drawing Club",
        "title": "Fun Fact: Colors can tell stories! 🎨",
        "body": "Did you know that warm colors like red and orange can make drawings feel happy and energetic?\n\nTry drawing your favorite animal using only warm colors today!\n\nSources:\n- Creative Bloq",
        "post_type": PostType.FUN_FACT,
        "status": PostStatus.PUBLISHED,
    },
    {
        "community_match": "Entrepreneurs",
        "title": "Startup funding is booming — what's your biggest fundraising lesson?",
        "body": "Q1 2026 saw record startup funding levels, with AI and climate tech leading the way.\n\nWhat's the most important lesson you've learned about fundraising?\n\nSources:\n- TechCrunch",
        "post_type": PostType.COMMUNITY_QUESTION,
        "status": PostStatus.PUBLISHED,
    },
    {
        "community_match": "France National Team Fans",
        "title": "Good Morning, Les Bleus fans! ☀️",
        "body": "Here are today's top updates:\n\n• Squad announcements and training camp news\n• Upcoming fixture previews\n• Fan discussion highlights\n\nWhat are you most excited about today?",
        "post_type": PostType.MORNING_UPDATE,
        "status": PostStatus.PUBLISHED,
    },
    {
        "community_match": "AI Enthusiasts",
        "title": "Evening Recap: AI News Roundup 🌙",
        "body": "Here's what happened today in AI:\n\n• New reasoning model breakthrough\n• Enterprise adoption trends\n• Open source community updates\n\nWhat should we discuss tomorrow?",
        "post_type": PostType.EVENING_RECAP,
        "status": PostStatus.PUBLISHED,
    },
    {
        "community_match": "Data Science Community",
        "title": "This Week in Data Science",
        "body": "📰 Top Story: New ML frameworks gaining traction\n💬 Most Discussed: Python vs R for analytics\n📅 Coming Up: Community AMA on career paths\n\nSources:\n- Dev.to",
        "post_type": PostType.WEEKLY_DIGEST,
        "status": PostStatus.PUBLISHED,
    },
]


from app.config import get_settings

settings = get_settings()


async def seed():
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Community).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded, skipping.")
            return

        print("Seeding communities...")
        community_map = {}
        for c_data in COMMUNITIES:
            community = Community(
                name=c_data["name"],
                description=c_data["description"],
                category=c_data["category"],
                country=c_data.get("country"),
                region=c_data.get("region"),
                preferred_tone=c_data.get("preferred_tone", "friendly"),
                is_child_safe=c_data.get("is_child_safe", False),
            )
            session.add(community)
            await session.flush()
            community_map[c_data["name"]] = community

            for tag in c_data["tags"]:
                session.add(CommunityTag(community_id=community.id, tag=tag))
            for topic in c_data["blocked_topics"]:
                session.add(CommunityBlockedTopic(community_id=community.id, topic=topic))

        print("Seeding sources...")
        source_map = {}
        for s_data in SOURCES:
            source = Source(**s_data)
            session.add(source)
            await session.flush()
            source_map[s_data["category"]] = source

        category_source_map = {
            "football": ["football", "sports"],
            "cricket": ["cricket", "sports"],
            "technology": ["technology"],
            "art": ["art"],
            "business": ["business"],
            "local": ["local"],
        }

        for c_name, community in community_map.items():
            cat = community.category
            for src_cat in category_source_map.get(cat, ["sports"]):
                if src_cat in source_map:
                    session.add(CommunitySource(community_id=community.id, source_id=source_map[src_cat].id))

        print("Seeding articles...")
        article_map = {}
        if settings.seed_sample_data:
            default_source = list(source_map.values())[0]
            for i, a_data in enumerate(SAMPLE_ARTICLES):
                src = source_map.get(a_data["category"], default_source)
                content_hash = hashlib.sha256(f"seed-{i}-{a_data['title']}".encode()).hexdigest()
                article = SourceArticle(
                    source_id=src.id,
                    source_name=a_data["source_name"],
                    source_url=f"https://example.com/article/{i}",
                    title=a_data["title"],
                    author="Editorial Team",
                    publication_date=datetime.now(timezone.utc) - timedelta(days=i),
                    category=a_data["category"],
                    topic=a_data["topic"],
                    raw_content=a_data["content"],
                    content_hash=content_hash,
                    is_processed=True,
                )
                session.add(article)
                await session.flush()
                article_map[a_data["title"]] = article

                session.add(AIAnalysis(
                    article_id=article.id,
                    topic=a_data["topic"],
                    entities=[a_data["topic"]],
                    people=["Player A"] if "football" in a_data["category"] or "cricket" in a_data["category"] else [],
                    locations=["Global"],
                    organizations=[a_data["source_name"]],
                    sentiment="positive",
                    keywords=a_data["topic"].split(),
                    relevance_score=Decimal("0.92"),
                    provider="mock",
                    model="mock-v1",
                ))
                session.add(AISummary(
                    article_id=article.id,
                    short_summary=a_data["content"][:200],
                    medium_summary=a_data["content"],
                    long_summary=a_data["content"],
                    provider="mock",
                    model="mock-v1",
                ))

            print("Seeding posts...")
            for p_data in SAMPLE_POSTS:
                community = community_map.get(p_data["community_match"])
                if not community:
                    continue

                article_title = next(
                    (t for t in article_map if community.category in article_map[t].category),
                    list(article_map.keys())[0],
                )
                article = article_map[article_title]

                post = GeneratedPost(
                    community_id=community.id,
                    article_id=article.id,
                    title=p_data["title"],
                    body=p_data["body"],
                    post_type=p_data["post_type"],
                    tone=community.preferred_tone,
                    hashtags=[f"#{community.category}", f"#{community.name.replace(' ', '')}"],
                    poll_options=p_data.get("poll_options"),
                    status=p_data["status"],
                    published_at=datetime.now(timezone.utc) - timedelta(hours=SAMPLE_POSTS.index(p_data) * 2),
                    provider="mock",
                    model="mock-v1",
                )
                session.add(post)
                await session.flush()

                session.add(PostSource(
                    post_id=post.id,
                    source_name=article.source_name,
                    source_url=article.source_url,
                    article_id=article.id,
                ))
                session.add(ModerationResult(
                    post_id=post.id,
                    is_safe=True,
                    overall_score=Decimal("0.95"),
                    checks={"hate_speech": True, "harassment": True, "child_safety": True},
                    flags=[],
                    provider="mock",
                    model="mock-v1",
                ))

            print("Seeding analytics...")
            for c_name, community in community_map.items():
                session.add(Analytics(
                    community_id=community.id,
                    metric_date=datetime.now(timezone.utc).date(),
                    posts_generated=2,
                    posts_published=2,
                    post_type_breakdown={"news_discussion": 1, "community_question": 1},
                ))

            session.add(PublishingJob(
                job_type="seed_initial",
                status=JobStatus.COMPLETED,
                posts_generated=len(SAMPLE_POSTS),
                posts_published=len(SAMPLE_POSTS),
                articles_collected=len(SAMPLE_ARTICLES),
                started_at=datetime.now(timezone.utc) - timedelta(hours=1),
                completed_at=datetime.now(timezone.utc),
            ))
        else:
            print("Skipping sample articles and posts (SEED_SAMPLE_DATA=false).")

        print("Seeding AI provider settings...")
        for provider in ["mock", "openai", "anthropic", "gemini", "huggingface"]:
            session.add(AIProviderSetting(
                provider=provider,
                is_active=provider == "mock",
                is_default=provider == "mock",
                model="mock-v1" if provider == "mock" else None,
                temperature=Decimal("0.70"),
            ))

        await session.commit()
        if settings.seed_sample_data:
            print(f"Seeded {len(COMMUNITIES)} communities, {len(SOURCES)} sources, {len(SAMPLE_ARTICLES)} articles, {len(SAMPLE_POSTS)} posts.")
        else:
            print(f"Seeded {len(COMMUNITIES)} communities and {len(SOURCES)} sources (no sample posts).")


if __name__ == "__main__":
    asyncio.run(seed())
