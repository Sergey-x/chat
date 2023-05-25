import os
import time

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from chat.log import get_logger
from chat.settings import SETTINGS


logger = get_logger(__name__)


class MyDatabase:
    engine: AsyncEngine | None = None
    SessionLocal = None
    async_session = None
    Base = declarative_base()

    @classmethod
    def init(cls):
        """Set up database.
        Create connection pool.
        """
        if cls.engine is None:
            cls.engine = create_async_engine(SETTINGS.get_async_database_uri(), future=True, pool_size=20)  # noqa
        if cls.SessionLocal is None:
            cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        if cls.async_session is None:
            cls.async_session = sessionmaker(cls.engine, class_=AsyncSession, expire_on_commit=False)

    @classmethod
    def create_tables(cls):
        """Create tables in database if they do not exist."""
        while True:
            try:
                os.system('cd chat && alembic upgrade head')
                logger.debug("Migrations created!")
                break
            except OperationalError:
                logger.error("Try to create tables in 3s...")
                time.sleep(3)
            except BaseException as e:
                logger.error(e)
                logger.error("Try to create tables in 3s...")
                time.sleep(3)

    @classmethod
    async def finish(cls):
        """Dispose the connection pool."""
        if cls.engine is not None:
            await cls.engine.dispose()
            cls.engine = None
            cls.SessionLocal = None
            cls.async_session = None
