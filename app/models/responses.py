from __future__ import annotations

from datetime import datetime, timezone

from typing import Any

from pydantic import BaseModel, Field


class TaskQueuedResponse(BaseModel):
    task_id: str
    status: str = "queued"
    queued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None
