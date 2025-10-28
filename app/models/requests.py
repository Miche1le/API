from __future__ import annotations

from typing import Any

from pydantic import BaseModel, HttpUrl, field_validator

from app.core.config import settings


class ParseRequest(BaseModel):
    """Request payload for submitting a new parsing job."""

    url: HttpUrl
    parser_type: str = "default"
    metadata: dict[str, Any] | None = None

    @field_validator("url")
    @classmethod
    def validate_domain(cls, value: HttpUrl) -> HttpUrl:
        settings.validate_url(str(value))
        return value


class BulkParseRequest(BaseModel):
    """Accept multiple URLs in one request."""

    urls: list[HttpUrl]
    parser_type: str = "default"
    metadata: dict[str, Any] | None = None

    @field_validator("urls")
    @classmethod
    def ensure_non_empty(cls, value: list[HttpUrl]) -> list[HttpUrl]:
        if not value:
            raise ValueError("At least one URL must be provided.")
        for url in value:
            settings.validate_url(str(url))
        return value

