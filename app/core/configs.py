from decouple import config

from pydantic_settings import BaseSettings
from sqlalchemy.ext.declarative import declarative_base

from typing import ClassVar


class Settings(BaseSettings):
    """
    Configurações gerais usadas na aplicação
    """

    API_STR: str = "/api"
    TEST_MODE: bool = config("TEST_MODE", default=False, cast=bool)

    DBBaseModel: ClassVar = declarative_base()

    JWT_SECRET: str = config("SECRET_KEY")

    EMAIL: str = config("EMAIL")
    EMAIL_PASSWORD: str = config("EMAIL_PASSWORD")

    FRONT_URL: str = config("FRONT_URL")
    """
    import secrets

    token: str = secrets.token_urlsafe(32)
    """
    ALGORITHM: str = config("ALGORITHM")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    @property
    def DB_URL(self) -> str:
        return config("DB_URL_TEST") if self.TEST_MODE else config("DB_URL")

    class Config:
        case_sensitive = True


settings: Settings = Settings()
