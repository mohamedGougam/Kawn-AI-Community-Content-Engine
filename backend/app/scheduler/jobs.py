"""APScheduler background job service."""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.services.content_pipeline import ContentPipeline

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_settings = get_settings()


async def _run_source_collection():
    logger.info("Scheduler: collecting sources")
    async with AsyncSessionLocal() as session:
        from app.services.sources.collector import SourceCollector
        collector = SourceCollector(session)
        count = await collector.collect_all()
        await session.commit()
        logger.info("Collected %d new articles", count)


async def _run_content_generation():
    logger.info("Scheduler: generating content for active communities")
    async with AsyncSessionLocal() as session:
        pipeline = ContentPipeline(session)
        jobs = await pipeline.run_full_pipeline()
        await session.commit()
        logger.info("Completed %d community pipeline jobs", len(jobs))


async def _run_hourly_generation():
    logger.info("Scheduler: hourly post generation")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from app.models import Community

        result = await session.execute(
            select(Community).where(Community.is_active == True)  # noqa: E712
        )
        communities = result.scalars().all()
        pipeline = ContentPipeline(session)

        for community in communities:
            await pipeline.generate_post(community.id)

        await session.commit()
        logger.info("Generated posts for %d communities", len(communities))


def start_scheduler():
    if not _settings.scheduler_enabled:
        logger.info("Scheduler disabled")
        return

    scheduler.add_job(
        _run_source_collection,
        IntervalTrigger(minutes=30),
        id="source_collection",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )

    scheduler.add_job(
        _run_hourly_generation,
        CronTrigger(minute=0),
        id="hourly_generation",
        replace_existing=True,
    )

    scheduler.add_job(
        _run_content_generation,
        CronTrigger(hour=6, minute=0),
        id="daily_full_pipeline",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
