# --------------------------------------------------------------------------
# Configuration module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import os
import secrets
import warnings
from typing import Annotated, Any, Literal, Optional

from pydantic import (
    AnyUrl,
    BeforeValidator,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # .env path : 프로젝트 루트
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENVIRONMENT: Literal["development", "production"] = "development"

    CLIENT_ORIGIN: str = ""  # for web playground application (not sure)

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = (
        []
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.CLIENT_ORIGIN
        ]

    PROJECT_NAME: str = "Qshing Server"
    MODEL_NAME: str = "best_acc_model.pt"
    MODEL_PATH: str = os.path.join(
        os.path.dirname(__file__), "..", "service", "model", MODEL_NAME
    )

    HTML_LOAD_TIMEOUT: int = 30  # seconds
    HTML_LOAD_RETRIES: int = 3

    CHROME_BIN: str = "/usr/bin/chromium"
    CHROMEDRIVER_PATH: str = "/usr/bin/chromedriver"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_CACHE_TTL: int = 86400  # 1일

    # PostgreSQL
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "phishing_data"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def POSTGRES_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(  # type: ignore
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # MongoDB
    MONGODB_USER: str = "admin"
    MONGODB_PASSWORD: str = "password"
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_NAME: str = "phishing_feedback"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def MONGODB_URI(self) -> str:
        return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_NAME}"

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "development":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)

        return self


settings = Settings()  # type: ignore
