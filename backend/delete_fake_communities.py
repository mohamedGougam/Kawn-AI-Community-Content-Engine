import asyncio
from app.database import AsyncSessionLocal
from app.models import Community
from sqlalchemy import delete


async def main():
    async with AsyncSessionLocal() as session:
        print("Deleting fake/mock communities from database...")
        res = await session.execute(
            delete(Community).where(Community.kawn_community_id == None)
        )
        await session.commit()
        print("Done. Fake communities removed.")

if __name__ == "__main__":
    asyncio.run(main())
