from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_parser_client, get_task_dispatcher, get_task_state_repository
from app.models.requests import BulkParseRequest, ParseRequest
from app.models.responses import TaskQueuedResponse, TaskStatusResponse
from app.services.parser_client import ParserClient
from app.services.task_dispatcher import TaskDispatcher, TaskEnvelope
from app.services.task_state import TaskState, TaskStateRepository


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/healthz", tags=["meta"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/parse", response_model=TaskQueuedResponse, status_code=status.HTTP_202_ACCEPTED, tags=["parsing"])
async def enqueue_parse_request(
    request: ParseRequest,
    dispatcher: TaskDispatcher = Depends(get_task_dispatcher),
    state_repo: TaskStateRepository = Depends(get_task_state_repository),
) -> TaskQueuedResponse:
    task_id = str(uuid4())
    envelope = TaskEnvelope(
        task_id=task_id,
        url=str(request.url),
        parser_type=request.parser_type,
        metadata=request.metadata,
    )
    await dispatcher.publish(envelope)
    await state_repo.set_state(TaskState(task_id=task_id, status="queued"))
    logger.info("Enqueued parsing task %s for %s", task_id, request.url)
    return TaskQueuedResponse(task_id=task_id)


@router.post(
    "/parse/bulk",
    response_model=list[TaskQueuedResponse],
    status_code=status.HTTP_202_ACCEPTED,
    tags=["parsing"],
)
async def enqueue_bulk_parse_request(
    request: BulkParseRequest,
    dispatcher: TaskDispatcher = Depends(get_task_dispatcher),
    state_repo: TaskStateRepository = Depends(get_task_state_repository),
) -> list[TaskQueuedResponse]:
    responses: list[TaskQueuedResponse] = []
    for url in request.urls:
        task_id = str(uuid4())
        envelope = TaskEnvelope(
            task_id=task_id,
            url=str(url),
            parser_type=request.parser_type,
            metadata=request.metadata,
        )
        await dispatcher.publish(envelope)
        await state_repo.set_state(TaskState(task_id=task_id, status="queued"))
        responses.append(TaskQueuedResponse(task_id=task_id))
    return responses


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatusResponse,
    tags=["parsing"],
)
async def get_task_status(
    task_id: str,
    state_repo: TaskStateRepository = Depends(get_task_state_repository),
) -> TaskStatusResponse:
    state = await state_repo.get_state(task_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return TaskStatusResponse(
        task_id=state.task_id,
        status=state.status,
        result=state.result,
        error=state.error,
    )


@router.get(
    "/preview",
    tags=["parsing"],
)
async def preview_url(
    url: str,
    parser: ParserClient = Depends(get_parser_client),
) -> dict[str, str]:
    content = await parser.fetch_html(url)
    return {"url": url, "content_snippet": content[:500]}
