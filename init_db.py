import asyncio
from app.core.database import engine, Base
import app.models  # Ensure all models are imported so Base.metadata knows about them

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(create_tables())
