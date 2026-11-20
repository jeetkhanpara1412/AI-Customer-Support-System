from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/app"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "development-only-change-me"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cors_origins: str | list[str] = "http://localhost:5173"
    env: str = "development"
    answer_confidence_threshold: float = 0.60
    answer_similarity_threshold: float = 0.45
    clarify_confidence_threshold: float = 0.35
    admin_email: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ADMIN_EMAIL", "FIRST_ADMIN_EMAIL"),
    )
    admin_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ADMIN_PASSWORD", "FIRST_ADMIN_PASSWORD"),
    )
    admin_name: str = "Support Administrator"
    demo_user_email: str | None = None
    demo_user_password: str | None = None
    demo_user_name: str = "Demo Customer"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def require_explicit_origins(cls, origins: str | list[str]) -> str | list[str]:
        values = origins.split(",") if isinstance(origins, str) else origins
        if not values or any(origin.strip() == "*" for origin in values):
            raise ValueError(
                "CORS_ORIGINS must contain explicit origins and cannot include '*'"
            )
        return origins

    @property
    def cors_origin_list(self) -> list[str]:
        if isinstance(self.cors_origins, str):
            return [
                origin.strip()
                for origin in self.cors_origins.split(",")
                if origin.strip()
            ]
        return self.cors_origins

    @model_validator(mode="after")
    def reject_weak_production_secret(self) -> "Settings":
        if self.env.lower() == "production" and (
            self.jwt_secret == "development-only-change-me"
            or len(self.jwt_secret) < 32
            or "replace-with" in self.jwt_secret.lower()
            or "changeme" in self.jwt_secret.lower()
        ):
            raise ValueError("JWT_SECRET must be at least 32 characters in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
