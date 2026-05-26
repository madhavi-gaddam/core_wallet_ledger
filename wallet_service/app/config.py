from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Wallet & Ledger Service"
    app_env: str = "development"
    debug: bool = Field(default=True, validation_alias="APP_DEBUG")
    database_url: str
    secret_key: str = Field(
        default="change-this-secret-key",
        validation_alias="SECRET_KEY",
    )
    algorithm: str = Field(default="HS256", validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    allowed_origins_csv: str = Field(
        default="",
        validation_alias="ALLOWED_ORIGINS",
    )
    allowed_hosts_csv: str = Field(
        default="*",
        validation_alias="ALLOWED_HOSTS",
    )
    docs_enabled: bool = Field(default=True, validation_alias="DOCS_ENABLED")

    @property
    def allowed_origins(self) -> list[str]:
        return self._parse_csv(self.allowed_origins_csv)

    @property
    def allowed_hosts(self) -> list[str]:
        return self._parse_csv(self.allowed_hosts_csv) or ["*"]

    @staticmethod
    def _parse_csv(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.app_env.lower() == "production":
            if self.secret_key == "change-this-secret-key":
                raise ValueError("SECRET_KEY must be set in production.")
            if len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters.")
            if self.debug:
                raise ValueError("APP_DEBUG must be False in production.")
        return self

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
