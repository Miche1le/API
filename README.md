# API

Внутренний сервис принимает URL от пользователя и отправляет их в очередь на обработку. FastAPI отдает эндпоинты, HTTPX вытягивает страницы, RabbitMQ раздает задания воркерам, Redis хранит статусы.

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
| GET   | `/healthz` | Проверка доступности |
| POST  | `/parse` | Поставить один URL в очередь, вернуть `task_id` |
| POST  | `/parse/bulk` | Отправить список ссылок |
| GET   | `/tasks/{task_id}` | Получить статус задачи |
| GET   | `/preview?url=` | Получить HTML (только для внутреннего теста) |
