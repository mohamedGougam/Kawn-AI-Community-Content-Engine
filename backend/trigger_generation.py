import asyncio
from app.database import AsyncSessionLocal
from app.services.content_pipeline import ContentPipeline


async def main():
    async with AsyncSessionLocal() as session:
        pipeline = ContentPipeline(session)
        print("Running full content generation pipeline...")
        jobs = await pipeline.run_full_pipeline()
        await session.commit()
        print(f"Pipeline completed. Generated posts for {len(jobs)} communities.")

if __name__ == "__main__":
    asyncio.run(main())
