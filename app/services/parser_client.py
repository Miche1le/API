from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.core.config import Settings


logger = logging.getLogger(__name__)


class ParserClient(httpx.AsyncClient):
    """
    HTTPX client specialized for fetching upstream pages that will later be parsed.

    The client reuses connections across requests and implements a simple retry
    loop to mitigate transient upstream failures.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        super().__init__(
            timeout=httpx.Timeout(settings.http_timeout),
            headers={
                "User-Agent": settings.parser_user_agent,
                "Accept": "*/*",
            },
            follow_redirects=True,
        )

    async def fetch_html(self, url: str, *, max_retries: int | None = None) -> str:
        """Fetch raw HTML from the supplied URL with optional retries."""
        response = await self._request_with_retry("GET", url, max_retries=max_retries)
        return response.text

    async def fetch_json(self, url: str, *, max_retries: int | None = None) -> Any:
        """Fetch JSON payload from the supplied URL with optional retries."""
        response = await self._request_with_retry("GET", url, max_retries=max_retries)
        return response.json()

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        max_retries: int | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Perform an HTTP request with a naive exponential backoff policy."""
        self._settings.validate_url(url)

        retries = self._settings.http_max_retries if max_retries is None else max_retries
        delay = 0.5
        attempt = 0
        last_exc: Exception | None = None

        while attempt <= retries:
            try:
                response = await self.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                # Re-raise immediately for client errors to avoid hitting robots/ban policies.
                if 400 <= exc.response.status_code < 500:
                    raise
                last_exc = exc
            except httpx.TransportError as exc:
                last_exc = exc

            attempt += 1
            if attempt > retries:
                break

            logger.warning(
                "Request to %s failed (%s). Retrying in %.1fs (attempt %s/%s).",
                url,
                last_exc,
                delay,
                attempt,
                retries,
            )
            await asyncio.sleep(delay)
            delay *= 2

        assert last_exc is not None  # for type checkers
        raise last_exc

