from functools import lru_cache

import pydantic as pd
from dotenv import load_dotenv
from enums import Stages
from log import get_logger


logger = get_logger(__name__)

load_dotenv()


def validate_env_var(varname, v):
    if not v:
        raise ValueError(f"`{varname}` variable is empty")
    return v


class Settings(pd.BaseSettings):
    STAGE: Stages = Stages.PROD

    # ENVS for connecting to postgres
    CHAT_POSTGRES_DBNAME: str | None
    CHAT_POSTGRES_USER: str | None
    CHAT_POSTGRES_PASSWORD: str | None
    CHAT_POSTGRES_HOST: str | None
    CHAT_POSTGRES_PORT: int = 5432

    @pd.validator("CHAT_POSTGRES_DBNAME")
    def validate_chat_postgres_dbname_not_empty(cls, v: str):
        return validate_env_var('CHAT_POSTGRES_DBNAME', v)

    @pd.validator("CHAT_POSTGRES_USER")
    def validate_chat_postgres_user_not_empty(cls, v: str):
        return validate_env_var('CHAT_POSTGRES_USER', v)

    @pd.validator("CHAT_POSTGRES_PASSWORD")
    def validate_chat_postgres_password_not_empty(cls, v: str):
        return validate_env_var('CHAT_POSTGRES_PASSWORD', v)

    @property
    def database_settings(self) -> dict:
        """
        Get all settings for connection with database.
        """
        return {
            "database": self.CHAT_POSTGRES_DBNAME,
            "user": self.CHAT_POSTGRES_USER,
            "password": self.CHAT_POSTGRES_PASSWORD,
            "host": self.CHAT_POSTGRES_HOST,
            "port": self.CHAT_POSTGRES_PORT,
        }

    def get_sync_database_uri(self):
        return "postgresql://{user}:{password}@{host}:{port}/{database}".format(
            **self.database_settings,
        )

    def get_async_database_uri(self):
        logger.debug("Use asyncpg driver for db access")
        return "postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}".format(
            **self.database_settings,
        )

    class Config:
        env_file = '.env'


@lru_cache
def get_settings() -> Settings:
    return Settings()


SETTINGS: Settings = get_settings()
