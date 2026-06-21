"""Admin utility routes."""

from fastapi import APIRouter

from app.reset_content import reset_content

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/reset-content")
async def reset_all_content():
    """Remove all posts, articles, analytics, and job history. Keeps communities and sources."""
    counts = await reset_content()
    return {
        "message": "Content reset complete. Communities and sources were kept.",
        "deleted": counts,
    }
