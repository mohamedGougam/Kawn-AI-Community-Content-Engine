"""Publish approved posts to Kawn App communities."""

import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings
from app.models import Community, GeneratedPost

logger = logging.getLogger(__name__)


class KawnPublishError(Exception):
    """Raised when a post cannot be published to the Kawn App."""


@dataclass
class KawnPublishResult:
    kawn_post_id: str
    kawn_community_id: str


class KawnAppPublisher:
    """Sends generated posts to the Kawn App community feed."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_url = (settings.kawn_app_api_url or "").rstrip("/")
        self.api_key = settings.kawn_app_api_key
        self.enabled = bool(self.api_url and self.api_key)

    def _community_external_id(self, community: Community) -> str:
        if community.kawn_community_id:
            return community.kawn_community_id
        raise KawnPublishError(
            f"Community '{community.name}' has no Kawn App ID. "
            "Set kawn_community_id on the community before publishing."
        )

    async def publish_post(self, community: Community, post: GeneratedPost) -> KawnPublishResult:
        if not self.enabled:
            raise KawnPublishError(
                "Kawn App API is not configured. Set KAWN_APP_API_URL and KAWN_APP_API_KEY."
            )

        community_id = self._community_external_id(community)
        payload = {
            "title": post.title,
            "body": post.body,
            "post_type": post.post_type.value,
            "tone": post.tone,
            "hashtags": post.hashtags or [],
            "poll_options": post.poll_options,
            "source_engine_post_id": str(post.id),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.api_url}/api/v1/communities/{community_id}/posts"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            body = e.response.text[:300] if e.response else ""
            raise KawnPublishError(f"Kawn App API error ({e.response.status_code}): {body}") from e
        except httpx.RequestError as e:
            raise KawnPublishError(f"Could not reach Kawn App API: {e}") from e

        kawn_post_id = str(data.get("id") or data.get("post_id") or "")
        if not kawn_post_id:
            raise KawnPublishError("Kawn App API did not return a post id.")

        logger.info(
            "Published post %s to Kawn community %s as %s",
            post.id,
            community_id,
            kawn_post_id,
        )
        return KawnPublishResult(kawn_post_id=kawn_post_id, kawn_community_id=community_id)


def get_kawn_publisher() -> KawnAppPublisher:
    return KawnAppPublisher()
