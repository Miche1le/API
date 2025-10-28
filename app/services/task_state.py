from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TaskState:
    task_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


class TaskStateRepository:
    async def set_state(self, state: TaskState) -> None:
        raise NotImplementedError

    async def get_state(self, task_id: str) -> TaskState | None:
        raise NotImplementedError


class RedisTaskStateRepository(TaskStateRepository):
    def __init__(self, redis_url: str):
        if aioredis is None:
            raise RuntimeError("redis-py[asyncio] is required for RedisTaskStateRepository. Install via 'pip install redis'.")

        self._client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def set_state(self, state: TaskState) -> None:
        await self._client.hset(
            state.task_id,
            mapping={
                "status": state.status,
                "result": json.dumps(state.result) if state.result is not None else "",
                "error": state.error or "",
            },
        )

    async def get_state(self, task_id: str) -> TaskState | None:
        payload = await self._client.hgetall(task_id)
        if not payload:
            return None
        result = payload.get("result") or None
        return TaskState(
            task_id=task_id,
            status=payload.get("status", "unknown"),
            result=json.loads(result) if result else None,
            error=payload.get("error") or None,
        )


class InMemoryTaskStateRepository(TaskStateRepository):
    def __init__(self):
        self._store: dict[str, TaskState] = {}

    async def set_state(self, state: TaskState) -> None:
        logger.debug("Caching task state in memory: %s -> %s", state.task_id, state.status)
        self._store[state.task_id] = state

    async def get_state(self, task_id: str) -> TaskState | None:
        return self._store.get(task_id)
