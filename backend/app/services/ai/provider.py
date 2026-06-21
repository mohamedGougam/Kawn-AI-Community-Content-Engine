"""AI provider abstraction layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
import logging
import os
import random
import re

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    topic: str
    entities: list[str] = field(default_factory=list)
    people: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    sentiment: str = "neutral"
    keywords: list[str] = field(default_factory=list)
    relevance_score: float = 0.8


@dataclass
class SummaryResult:
    short_summary: str
    medium_summary: str
    long_summary: str


@dataclass
class GeneratedPostResult:
    title: str
    body: str
    post_type: str
    tone: str
    hashtags: list[str] = field(default_factory=list)
    poll_options: list[str] | None = None


@dataclass
class ModerationResultData:
    is_safe: bool
    overall_score: float
    checks: dict
    flags: list[str] = field(default_factory=list)
    reason: str | None = None


class AIProvider(ABC):
    name: str = "base"
    model: str = "unknown"

    @abstractmethod
    async def analyze_content(self, title: str, content: str, community_context: dict) -> AnalysisResult:
        pass

    @abstractmethod
    async def summarize(self, title: str, content: str) -> SummaryResult:
        pass

    @abstractmethod
    async def generate_post(
        self,
        community: dict,
        article: dict,
        analysis: AnalysisResult,
        summary: SummaryResult,
        post_type: str,
    ) -> GeneratedPostResult:
        pass

    @abstractmethod
    async def moderate(self, title: str, body: str, is_child_safe: bool = False) -> ModerationResultData:
        pass

    @staticmethod
    def _parse_json(text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        return json.loads(text)


class MockAIProvider(AIProvider):
    """Deterministic mock provider for local development without API keys."""

    name = "mock"
    model = "mock-v1"

    async def analyze_content(self, title: str, content: str, community_context: dict) -> AnalysisResult:
        category = community_context.get("category", "general")
        keywords = [w for w in title.lower().split() if len(w) > 4][:5]
        return AnalysisResult(
            topic=category,
            entities=keywords[:3],
            people=["Player A", "Coach B"] if "football" in category or "cricket" in category else [],
            locations=[community_context.get("country", "Global") or "Global"],
            organizations=[community_context.get("name", "Community")],
            sentiment=random.choice(["positive", "neutral", "excited"]),
            keywords=keywords,
            relevance_score=round(random.uniform(0.7, 0.98), 2),
        )

    async def summarize(self, title: str, content: str) -> SummaryResult:
        base = content or title
        words = base.split()
        short = " ".join(words[:50])
        medium = " ".join(words[:150])
        long = " ".join(words[:300])
        return SummaryResult(short_summary=short, medium_summary=medium, long_summary=long)

    async def generate_post(
        self,
        community: dict,
        article: dict,
        analysis: AnalysisResult,
        summary: SummaryResult,
        post_type: str,
    ) -> GeneratedPostResult:
        name = community.get("name", "Community")
        title_text = article.get("title", "Community Update")
        source = article.get("source_name", "Trusted Source")

        templates = {
            "news_discussion": (
                f"{title_text} — What do you think?",
                f"According to {source}, {summary.short_summary}\n\nWhat are your thoughts on this? Share your perspective with fellow {name} members!",
            ),
            "poll": (
                f"Community Poll: {analysis.topic.title()}",
                f"Based on recent news from {source}, we'd love your input!\n\nWhat's your take on the latest developments?",
                ["Option A", "Option B", "Option C"],
            ),
            "match_prediction": (
                "Match Prediction Time!",
                f"With the latest updates from {source}, it's time to predict!\n\nWhat score do you think we'll see? Drop your predictions below!",
            ),
            "community_question": (
                f"Question for {name}",
                f"What has been your favorite moment related to {analysis.topic}? We'd love to hear your stories and memories!",
            ),
            "fun_fact": (
                f"Did You Know? — {name}",
                f"Here's an interesting fact for our community: {summary.short_summary}\n\nDid you already know this? Tell us in the comments!",
            ),
            "weekly_digest": (
                f"This Week in {name}",
                f"📰 Top Story: {title_text}\n💬 Most Discussed: {analysis.topic}\n📅 Coming Up: Stay tuned for more updates!\n\nSources: {source}",
            ),
            "morning_update": (
                f"Good Morning, {name}! ☀️",
                f"Here are today's top updates:\n\n• {summary.short_summary}\n\nWhat are you most excited about today?",
            ),
            "evening_recap": (
                f"Evening Recap — {name} 🌙",
                f"Here's what happened today:\n\n{summary.medium_summary}\n\nWhat should we discuss tomorrow?",
            ),
        }

        tmpl = templates.get(post_type, templates["news_discussion"])
        poll_opts = tmpl[2] if len(tmpl) > 2 else None
        hashtags = [f"#{community.get('category', 'community').replace(' ', '')}", f"#{name.replace(' ', '')}"]

        return GeneratedPostResult(
            title=tmpl[0],
            body=tmpl[1],
            post_type=post_type,
            tone=community.get("preferred_tone", "friendly"),
            hashtags=hashtags,
            poll_options=poll_opts,
        )

    async def moderate(self, title: str, body: str, is_child_safe: bool = False) -> ModerationResultData:
        unsafe_words = ["hate", "violence", "explicit", "spam", "extremist"]
        text = (title + " " + body).lower()
        flags = [w for w in unsafe_words if w in text]

        checks = {
            "hate_speech": "hate" not in text,
            "harassment": True,
            "racism": True,
            "misinformation": True,
            "spam": "spam" not in text,
            "political_extremism": "extremist" not in text,
            "child_safety": len(flags) == 0 if is_child_safe else True,
            "profanity": True,
            "adult_content": "explicit" not in text,
            "violence": "violence" not in text,
        }

        is_safe = all(checks.values())
        return ModerationResultData(
            is_safe=is_safe,
            overall_score=0.95 if is_safe else 0.3,
            checks=checks,
            flags=flags,
            reason=None if is_safe else f"Flagged content: {', '.join(flags)}",
        )


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self):
        settings = get_settings()
        self.model = settings.openai_model
        self._client = None
        if settings.openai_api_key:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def _chat(self, system: str, user: str) -> str:
        if not self._client:
            raise RuntimeError("OpenAI API key not configured")
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or ""

    async def _safe_parse(self, raw: str, fallback_fn, *args, **kwargs):
        try:
            return self._parse_json(raw)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("OpenAI JSON parse failed, using fallback: %s", e)
            return await fallback_fn(*args, **kwargs)

    async def analyze_content(self, title: str, content: str, community_context: dict) -> AnalysisResult:
        mock = MockAIProvider()
        if not self._client:
            return await mock.analyze_content(title, content, community_context)
        prompt = f"Analyze this article for community '{community_context.get('name')}':\nTitle: {title}\nContent: {content[:2000]}\nReturn JSON with: topic, entities, people, locations, organizations, sentiment, keywords, relevance_score"
        raw = await self._chat("You are a content analyst. Return valid JSON only.", prompt)
        try:
            data = self._parse_json(raw)
        except (json.JSONDecodeError, KeyError, TypeError):
            return await mock.analyze_content(title, content, community_context)
        return AnalysisResult(
            topic=data.get("topic", "general"),
            entities=data.get("entities", []),
            people=data.get("people", []),
            locations=data.get("locations", []),
            organizations=data.get("organizations", []),
            sentiment=data.get("sentiment", "neutral"),
            keywords=data.get("keywords", []),
            relevance_score=float(data.get("relevance_score", 0.8)),
        )

    async def summarize(self, title: str, content: str) -> SummaryResult:
        mock = MockAIProvider()
        if not self._client:
            return await mock.summarize(title, content)
        prompt = f"Summarize:\nTitle: {title}\nContent: {content[:3000]}\nReturn JSON: short_summary (50 words max), medium_summary (150 words max), long_summary (300 words max)"
        raw = await self._chat("You are a summarizer. Return valid JSON only.", prompt)
        try:
            data = self._parse_json(raw)
            return SummaryResult(**data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return await mock.summarize(title, content)

    async def generate_post(self, community, article, analysis, summary, post_type) -> GeneratedPostResult:
        mock = MockAIProvider()
        if not self._client:
            return await mock.generate_post(community, article, analysis, summary, post_type)
        prompt = f"""Generate a {post_type} community post.
Community: {community}
Article: {article.get('title')}
Summary: {summary.short_summary}
Analysis topic: {analysis.topic}
Return JSON: title, body, post_type, tone, hashtags (array), poll_options (array or null)
Rules: Never copy verbatim. Add engagement question. Include source attribution in body."""
        raw = await self._chat("You are a community content creator. Return valid JSON only.", prompt)
        try:
            data = self._parse_json(raw)
            return GeneratedPostResult(**data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return await mock.generate_post(community, article, analysis, summary, post_type)

    async def moderate(self, title: str, body: str, is_child_safe: bool = False) -> ModerationResultData:
        mock = MockAIProvider()
        if not self._client:
            return await mock.moderate(title, body, is_child_safe)
        prompt = f"Moderate this post. Child-safe required: {is_child_safe}\nTitle: {title}\nBody: {body}\nReturn JSON: is_safe, overall_score, checks (object), flags (array), reason"
        raw = await self._chat("You are a content moderator. Return valid JSON only.", prompt)
        try:
            data = self._parse_json(raw)
            return ModerationResultData(**data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return await mock.moderate(title, body, is_child_safe)


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self):
        settings = get_settings()
        self.model = settings.anthropic_model
        self._client = None
        if settings.anthropic_api_key:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def _chat(self, system: str, user: str) -> str:
        if not self._client:
            raise RuntimeError("Anthropic API key not configured")
        resp = await self._client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text

    async def analyze_content(self, title, content, community_context) -> AnalysisResult:
        mock = MockAIProvider()
        if not self._client:
            return await mock.analyze_content(title, content, community_context)
        raw = await self._chat("Return JSON only.", f"Analyze: {title}\n{content[:2000]}")
        data = self._parse_json(raw)
        return AnalysisResult(
            topic=data.get("topic", "general"),
            entities=data.get("entities", []),
            people=data.get("people", []),
            locations=data.get("locations", []),
            organizations=data.get("organizations", []),
            sentiment=data.get("sentiment", "neutral"),
            keywords=data.get("keywords", []),
            relevance_score=data.get("relevance_score", 0.8),
        )

    async def summarize(self, title, content) -> SummaryResult:
        mock = MockAIProvider()
        if not self._client:
            return await mock.summarize(title, content)
        raw = await self._chat("Return JSON with short_summary, medium_summary, long_summary.", f"{title}\n{content[:3000]}")
        data = self._parse_json(raw)
        return SummaryResult(**data)

    async def generate_post(self, community, article, analysis, summary, post_type) -> GeneratedPostResult:
        mock = MockAIProvider()
        if not self._client:
            return await mock.generate_post(community, article, analysis, summary, post_type)
        raw = await self._chat("Return JSON: title, body, post_type, tone, hashtags, poll_options.", f"Create {post_type} for {community.get('name')}: {summary.short_summary}")
        data = self._parse_json(raw)
        return GeneratedPostResult(**data)

    async def moderate(self, title, body, is_child_safe=False) -> ModerationResultData:
        mock = MockAIProvider()
        if not self._client:
            return await mock.moderate(title, body, is_child_safe)
        raw = await self._chat("Return JSON: is_safe, overall_score, checks, flags, reason.", f"Moderate: {title}\n{body}")
        data = self._parse_json(raw)
        return ModerationResultData(**data)


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self):
        settings = get_settings()
        self.model = settings.gemini_model
        self._model = None
        if settings.google_api_key:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            self._model = genai.GenerativeModel(self.model)

    async def _generate(self, prompt: str) -> str:
        if not self._model:
            raise RuntimeError("Google API key not configured")
        resp = await self._model.generate_content_async(prompt)
        return resp.text

    async def analyze_content(self, title, content, community_context) -> AnalysisResult:
        mock = MockAIProvider()
        if not self._model:
            return await mock.analyze_content(title, content, community_context)
        raw = await self._generate(f"Analyze as JSON: {title}\n{content[:2000]}")
        data = self._parse_json(raw)
        return AnalysisResult(
            topic=data.get("topic", "general"),
            entities=data.get("entities", []),
            people=data.get("people", []),
            locations=data.get("locations", []),
            organizations=data.get("organizations", []),
            sentiment=data.get("sentiment", "neutral"),
            keywords=data.get("keywords", []),
            relevance_score=data.get("relevance_score", 0.8),
        )

    async def summarize(self, title, content) -> SummaryResult:
        mock = MockAIProvider()
        if not self._model:
            return await mock.summarize(title, content)
        raw = await self._generate(f"Summarize as JSON (short/medium/long): {title}\n{content[:3000]}")
        data = self._parse_json(raw)
        return SummaryResult(**data)

    async def generate_post(self, community, article, analysis, summary, post_type) -> GeneratedPostResult:
        mock = MockAIProvider()
        if not self._model:
            return await mock.generate_post(community, article, analysis, summary, post_type)
        raw = await self._generate(f"Create {post_type} post as JSON for {community.get('name')}: {summary.short_summary}")
        data = self._parse_json(raw)
        return GeneratedPostResult(**data)

    async def moderate(self, title, body, is_child_safe=False) -> ModerationResultData:
        mock = MockAIProvider()
        if not self._model:
            return await mock.moderate(title, body, is_child_safe)
        raw = await self._generate(f"Moderate as JSON: {title}\n{body}")
        data = self._parse_json(raw)
        return ModerationResultData(**data)


class HuggingFaceProvider(AIProvider):
    name = "huggingface"

    def __init__(self):
        settings = get_settings()
        self.model = settings.huggingface_model
        self._api_key = settings.huggingface_api_key
        self._mock = MockAIProvider()

    async def analyze_content(self, title, content, community_context) -> AnalysisResult:
        return await self._mock.analyze_content(title, content, community_context)

    async def summarize(self, title, content) -> SummaryResult:
        return await self._mock.summarize(title, content)

    async def generate_post(self, community, article, analysis, summary, post_type) -> GeneratedPostResult:
        return await self._mock.generate_post(community, article, analysis, summary, post_type)

    async def moderate(self, title, body, is_child_safe=False) -> ModerationResultData:
        return await self._mock.moderate(title, body, is_child_safe)


PROVIDERS: dict[str, type[AIProvider]] = {
    "mock": MockAIProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "huggingface": HuggingFaceProvider,
}


def get_ai_provider(provider_name: str | None = None) -> AIProvider:
    settings = get_settings()
    name = provider_name or settings.ai_default_provider

    # Auto-fallback to mock if real provider has no API key
    key_map = {
        "openai": settings.openai_api_key,
        "anthropic": settings.anthropic_api_key,
        "gemini": settings.google_api_key,
        "huggingface": settings.huggingface_api_key,
    }
    if name in key_map and not key_map[name]:
        name = "mock"

    cls = PROVIDERS.get(name, MockAIProvider)
    return cls()


def provider_has_key(provider_name: str) -> bool:
    settings = get_settings()
    env_map = {
        "openai": settings.openai_api_key,
        "anthropic": settings.anthropic_api_key,
        "gemini": settings.google_api_key,
        "huggingface": settings.huggingface_api_key,
        "mock": True,
    }
    return bool(env_map.get(provider_name, False))
