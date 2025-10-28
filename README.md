# API

Внутренний сервис для хакатона. Делает две вещи: принимает URL от пользователей и складывает их в очередь для воркеров, чтобы не тащить Selenium/парсер в бота. Код упакован в FastAPI, HTTPX ходит наружу, RabbitMQ раздаёт задачи, Redis (или in-memory) хранит статусы.

## Как устроено

- `ParserClient` — обёртка над HTTPX с повтором запросов и переиспользованием сессии.
- `TaskDispatcher` — лёгкий паблишер в RabbitMQ (`parser.tasks`, ключ `parse.*`).
- `TaskStateRepository` — статусы задач: Redis по умолчанию, in-memory в dev-режиме.
- Настройки лежат в `.env` (префикс `APP_`), см. `app/core/config.py`.

## Запуск локально

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Пример `.env`:

```
APP_ENVIRONMENT=development
APP_RABBITMQ_URL=amqp://guest:guest@localhost/
APP_REDIS_URL=redis://localhost:6379/0
APP_HTTP_TIMEOUT=10.0
APP_HTTP_MAX_RETRIES=3
APP_ALLOWED_DOMAINS=example.com,example.org
```

## REST-эндпоинты `/v1`

| Метод | Путь | Описание |
|-------|------|----------|
| GET   | `/healthz` | Простой пинг сервиса |
| POST  | `/parse` | Ставит один URL в очередь и возвращает `task_id` |
| POST  | `/parse/bulk` | Загружает пачку ссылок за один запрос |
| GET   | `/tasks/{task_id}` | Показывает статус задачи |
| GET   | `/preview?url=` | Быстрый просмотр HTML (только для внутренних проверок) |

## Что ещё сделать

1. Авторизация (хотя бы токен) на публичных ручках.
2. Боевой воркер, который берёт задания из RabbitMQ и пишет итог в Redis/БД.
3. Docker-compose для API + RabbitMQ + Redis и минимальный CI (lint + тесты).

Ветка `feature/parsing-api` готова к ревью и слиянию по git flow.
