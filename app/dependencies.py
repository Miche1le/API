from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.parser_client import ParserClient
from app.services.task_dispatcher import TaskDispatcher
from app.services.task_state import (
    InMemoryTaskStateRepository,
    RedisTaskStateRepository,
    TaskStateRepository,
)


async def get_parser_client(settings: Settings = Depends(get_settings)) -> AsyncGenerator[ParserClient, None]:
    client = ParserClient(settings)
    try:
        yield client
    finally:
        await client.aclose()


async def get_task_dispatcher(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[TaskDispatcher, None]:
    dispatcher = TaskDispatcher(settings)
    try:
        await dispatcher.connect()
        yield dispatcher
    finally:
        await dispatcher.close()


def get_task_state_repository(
    settings: Settings = Depends(get_settings),
) -> TaskStateRepository:
    try:
        return RedisTaskStateRepository(settings.redis_url)
    except RuntimeError:
        return InMemoryTaskStateRepository()

