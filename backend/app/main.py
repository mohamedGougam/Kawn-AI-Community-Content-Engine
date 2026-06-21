"""Kawn AI Community Content Engine - FastAPI Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, analytics, communities, posts, settings as ai_settings, sources
from app.config import get_settings
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.schemas import HealthResponse
from app.services.ai.provider import get_ai_provider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Kawn AI Community Content Engine...")
    start_scheduler()

    try:
        from app.seed import seed
        await seed()
    except Exception as e:
        logger.warning("Seed skipped or failed: %s", e)

    yield

    stop_scheduler()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Kawn AI Community Content Engine",
    description="AI-powered content generation engine for community posts",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(communities.router)
app.include_router(sources.router)
app.include_router(posts.router)
app.include_router(analytics.router)
app.include_router(ai_settings.router)
app.include_router(admin.router)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    from app.scheduler.jobs import scheduler

    provider = get_ai_provider()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        scheduler_running=scheduler.running,
        ai_provider=provider.name,
    )


@app.get("/", tags=["health"])
async def root():
    return {
        "name": "Kawn AI Community Content Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
