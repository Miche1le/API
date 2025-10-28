# Parsing API Service

Асинхронный сервис для постановки задач на парсинг сайтов. Сервис принимает запросы от пользователя, валидирует допустимость домена, сохраняет состояние задач и прокидывает их в RabbitMQ, откуда их забирают воркеры (Selenium, HTTP-parser, LLM и т.д. — см. диаграмму проекта).

## Архитектура

- **FastAPI** — HTTP-сервис для приёма запросов от фронта/ботов.
- **HTTPX** — переиспользуемый клиент (`ParserClient`) для загрузки HTML/JSON с целевых сайтов.
- **RabbitMQ** — `TaskDispatcher` публикует сообщения в exchange `parser.tasks`, далее задачи обрабатываются исполнителями (SEL, LLM и прочие).
- **Redis** — `TaskStateRepository` хранит статус задач; при отсутствии Redis автоматически используется in-memory реализация.
- **Config** — все параметры настраиваются через `.env` с префиксом `APP_` (см. `app/core/config.py`).

## Быстрый старт

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt

# Локальный запуск (по умолчанию FastAPI слушает 8000 порт)
uvicorn app.main:app --reload
```

Переменные окружения (пример `.env`):

```
APP_ENVIRONMENT=development
APP_RABBITMQ_URL=amqp://guest:guest@localhost/
APP_REDIS_URL=redis://localhost:6379/0
APP_HTTP_TIMEOUT=10.0
APP_HTTP_MAX_RETRIES=3
APP_ALLOWED_DOMAINS=example.com,example.org  # необязательный whitelist
```

## Основные REST-эндпоинты (`/v1`)

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/healthz` | Простой health-check. |
| `POST` | `/parse` | Поставить одну ссылку на парсинг. Возвращает `task_id`. |
| `POST` | `/parse/bulk` | Массовая постановка задач. |
| `GET` | `/tasks/{task_id}` | Статус задачи (queued / in_progress / done / failed). |
| `GET` | `/preview?url=...` | Быстро подтянуть HTML для дебага (не забываем ограничить доступ в проде). |

## Интеграция с воркерами

1. Воркеры подписываются на exchange `parser.tasks` с routing-key `parse.*`.
2. Получив задачу, воркер обрабатывает ссылку (HTTP парсер, Selenium, LLM и т.д.).
3. Результат складывается в Redis через `TaskStateRepository.set_state(TaskState(...))`, чтобы API `/tasks/{task_id}` возвращал актуальное состояние.

## Git flow

1. Основная разработка ведётся в ветке `develop`.
2. Фичи — в ветках вида `feature/<name>` (текущий код в `feature/parsing-api`).
3. Перед релизом мерджим в `release/x.y` и после тестирования — в `main`.

## Дальнейшие шаги

- Подключить авторизацию (JWT/Telegram OAuth) к публичным эндпоинтам.
- Реализовать воркеры (Selenium/Playwright) и интеграцию с RabbitMQ/Redis на прод-инфраструктуре.
- Настроить CI (линтеры, mypy, pytest) и контейнеризацию (Dockerfile + docker-compose).

