# API для парсинга

Проект обслуживает одну задачу — принимать ссылки от пользователей и раскладывать их по очередям на обработку. API асинхронный, построен на FastAPI и использует HTTPX для запросов к целевым сайтам. После постановки в очередь воркеры (Selenium/LLM/что угодно) разбирают задания и возвращают результат в Redis/БД — всё как на схеме проекта.

## Что внутри

- `ParserClient` на базе HTTPX тянет страницы, переиспользует пул соединений и делает повторные попытки при сетевых сбоях.
- `TaskDispatcher` публикует задания в RabbitMQ (`parser.tasks`, ключи `parse.*`).
- `TaskStateRepository` держит статусы задач: в продакшене через Redis, локально — in-memory fallback.
- Конфигурация подтягивается из `.env` с префиксом `APP_` (см. `app/core/config.py`).

## Как запустить локально

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Минимальный `.env`:

```
APP_ENVIRONMENT=development
APP_RABBITMQ_URL=amqp://guest:guest@localhost/
APP_REDIS_URL=redis://localhost:6379/0
APP_HTTP_TIMEOUT=10.0
APP_HTTP_MAX_RETRIES=3
APP_ALLOWED_DOMAINS=example.com,example.org
```

## REST-эндпоинты `/v1`

| Метод | Путь | Назначение |
|-------|------|------------|
| GET   | `/healthz` | Простой пинг |
| POST  | `/parse` | Ставит одну ссылку в очередь, возвращает `task_id` |
| POST  | `/parse/bulk` | Пакетная постановка ссылок |
| GET   | `/tasks/{task_id}` | Узнать статус задачи |
| GET   | `/preview?url=` | Быстрый просмотр HTML (только для внутреннего пользования) |

## Дальше по плану

1. Подружить API с авторизацией (JWT или токен).
2. Реализовать воркер, который забирает задания из RabbitMQ и обновляет статусы в Redis.
3. Собрать docker-compose и базовый CI (линтеры, pytest, mypy).

Фича лежит в `feature/parsing-api`, готова к ревью и интеграции по git flow.
