from __future__ import annotations

from functools import lru_cache
from typing import Iterable
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Parsing API"
    environment: str = "development"

    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost/")
    redis_url: str = Field(default="redis://localhost:6379/0")

    http_timeout: float = Field(default=10.0, gt=0)
    http_max_retries: int = Field(default=3, ge=0)
    parser_user_agent: str = Field(default="CourseParserBot/1.0")
    allowed_domains: list[str] = Field(default_factory=list)

    @field_validator("allowed_domains", mode="before")
    @classmethod
    def _split_allowed_domains(cls, value: str | Iterable[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return list(value)

    def is_domain_allowed(self, url: str) -> bool:
        if not self.allowed_domains:
            return True

        parsed = urlparse(url)
        host = parsed.hostname or ""
        return any(host == domain or host.endswith(f".{domain}") for domain in self.allowed_domains)

    def validate_url(self, url: str) -> str:
        if not self.is_domain_allowed(url):
            host = urlparse(url).hostname or ""
            raise ValueError(f"Domain '{host}' is not permitted for parsing.")
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
