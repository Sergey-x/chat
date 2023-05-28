from db.db import MyDatabase
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncSession:
    MyDatabase.init()
    async with MyDatabase.async_session() as session:
        yield session
