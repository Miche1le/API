from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

try:
    import aio_pika
except ImportError:
    aio_pika = None

from app.core.config import Settings


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TaskEnvelope:
    task_id: str
    url: str
    parser_type: str = "default"
    metadata: dict[str, Any] | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "task_id": self.task_id,
                "url": self.url,
                "parser_type": self.parser_type,
                "metadata": self.metadata or {},
            }
        )


class TaskDispatcher:
    def __init__(self, settings: Settings, exchange_name: str = "parser.tasks"):
        if aio_pika is None:
            raise RuntimeError("aio-pika is required for TaskDispatcher. Install it via 'pip install aio-pika'.")

        self._settings = settings
        self._exchange_name = exchange_name
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.Channel | None = None
        self._exchange: aio_pika.Exchange | None = None

    async def connect(self) -> None:
        if self._connection and not self._connection.is_closed:
            return

        logger.info("Connecting to RabbitMQ at %s", self._settings.rabbitmq_url)
        self._connection = await aio_pika.connect_robust(self._settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    async def publish(self, envelope: TaskEnvelope) -> None:
        if self._channel is None or self._exchange is None:
            await self.connect()

        assert self._channel is not None
        assert self._exchange is not None

        message = aio_pika.Message(
            body=envelope.to_json().encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        routing_key = f"parse.{envelope.parser_type}"
        logger.debug("Publishing task %s to %s", envelope.task_id, routing_key)
        await self._exchange.publish(message, routing_key=routing_key)

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
