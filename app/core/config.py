from __future__ import annotations

from functools import lru_cache
from typing import Iterable
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Parsing API"
    environment: str = "development"

    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost/",
        description="Connection string for RabbitMQ dispatcher.",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis instance used for task caching / deduplication.",
    )

    http_timeout: float = Field(
        default=10.0,
        gt=0,
        description="Default timeout (seconds) for upstream HTTP requests.",
    )
    http_max_retries: int = Field(
        default=3,
        ge=0,
        description="Number of retry attempts for transient upstream failures.",
    )
    parser_user_agent: str = Field(
        default="CourseParserBot/1.0",
        description="User-Agent header sent with outbound requests.",
    )
    allowed_domains: list[str] = Field(
        default_factory=list,
        description="Optional whitelist of domains allowed for parsing.",
    )

    @field_validator("allowed_domains", mode="before")
    @classmethod
    def _split_allowed_domains(cls, value: str | Iterable[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return list(value)

    def is_domain_allowed(self, url: str) -> bool:
        """Validate that the given URL matches the configured whitelist."""
        if not self.allowed_domains:
            return True

        parsed = urlparse(url)
        host = parsed.hostname or ""
        return any(host == domain or host.endswith(f".{domain}") for domain in self.allowed_domains)

    def validate_url(self, url: str) -> str:
        """Raise a descriptive error if the URL is not allowed."""
        if not self.is_domain_allowed(url):
            host = urlparse(url).hostname or ""
            raise ValueError(f"Domain '{host}' is not permitted for parsing.")
        return url


@lru_cache
def get_settings() -> Settings:
    """Cached accessor to avoid re-parsing env variables."""
    return Settings()


settings = get_settings()
