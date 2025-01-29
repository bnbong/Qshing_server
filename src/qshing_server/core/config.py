# --------------------------------------------------------------------------
# Configuration module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import os
import secrets
import warnings
from typing import Annotated, Any, Literal, Optional

from pydantic import AnyUrl, BeforeValidator, computed_field, model_validator
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
