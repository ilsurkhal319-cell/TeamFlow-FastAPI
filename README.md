# TeamFlow

Современный Kanban-сервис для командной работы на FastAPI и React.

## Возможности

- регистрация и вход по JWT;
- рабочие пространства и участники;
- Kanban-доски, участники и роли;
- задачи с приоритетом и комментариями;
- drag-and-drop между колонками;
- поиск и фильтрация досок и задач;
- комментарии и журнал активности;
- WebSocket-события для синхронизации доски;
- адаптивная тёмная панель управления;
- новый пользователь получает workspace «Основное» и стартовую Kanban-доску автоматически.

## Стек

FastAPI, SQLAlchemy 2, PostgreSQL, Alembic, Redis Pub/Sub, React, TypeScript, Vite, Lucide, CSS design system, Docker Compose.

## Архитектурные решения

```text
React → Nginx → FastAPI → PostgreSQL
                    └── Redis → WebSocket-события
```

### Авторизация

Пароли хешируются Argon2, а после регистрации или входа клиент получает JWT. React передаёт его в `Authorization: Bearer <token>`, а FastAPI через dependency `current_user` декодирует токен и загружает пользователя. Для WebSocket основной JWT не передаётся в URL: клиент получает одноразовый ticket, который хранится в Redis 60 секунд и удаляется при первом подключении.

### Разграничение доступа

Права проверяются на backend для каждого защищённого endpoint: владелец workspace управляет доской, а участник доски может работать только с доступными ему задачами и комментариями. Скрытие кнопок в React — лишь удобство интерфейса; оно не заменяет серверную проверку прав.

### Realtime

Изменение задачи сначала сохраняется в PostgreSQL, затем backend публикует короткое событие в Redis-канал конкретной доски. WebSocket-слой подписан на этот канал и пересылает событие всем открытым клиентам доски. PostgreSQL остаётся источником истины: Redis Pub/Sub используется для быстрой синхронизации, а после reconnect клиент повторно загружает актуальную доску.

### Слои backend

- `api/v1/endpoints` — HTTP-транспорт и маршруты;
- `schemas` — Pydantic-валидация запросов и ответов;
- `domain` — SQLAlchemy-модели и связи данных;
- `repositories` — повторно используемые запросы к данным;
- `services` — прикладные сценарии, например bootstrap нового пользователя и журнал активности;
- `realtime` — Redis Pub/Sub и WebSocket-транспорт.

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

React-интерфейс откроется на http://localhost:5173, документация API — на http://localhost:8001/docs.

Для локального запуска backend без Docker:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

В development-режиме при пустой базе автоматически создаётся демонстрационное пространство с доской и задачами. Публичная landing-страница не входит в аккаунт автоматически: демо запускается кнопкой «Попробовать демо». Каждая demo-сессия получает отдельного пользователя и рабочее пространство, токен действует 45 минут. В production демо отключается через `DEMO_ENABLED=false`.

## Структура проекта

```text
TeamFlow-FastAPI/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # HTTP endpoints by context
│   │   ├── core/               # settings, security, logging
│   │   ├── db/                 # engine and sessions
│   │   ├── domain/             # SQLAlchemy models
│   │   ├── repositories/       # persistence queries
│   │   ├── services/           # application use-cases
│   │   └── realtime/           # WebSocket transport
│   ├── migrations/
│   ├── scripts/entrypoint.sh
│   └── tests/
├── frontend-react/             # production React + Vite client
│   ├── index.html              # main application entrypoint (landing page)
│   ├── src/app/App.tsx         # React version of the original board.html UI
│   └── src/styles/              # shared TeamFlow design system
├── compose.yaml
└── .env.production.example
```

API запускает `alembic upgrade head` перед Uvicorn (в CI/CD можно отключить через `RUN_MIGRATIONS=false`). React собирается в неизменяемый статический артефакт и отдаётся Nginx-контейнером. Nginx проксирует API-запросы в FastAPI, а history fallback оставляет маршрутизацию на React-клиенте.

React-страница доски сохраняет исходную структуру TeamFlow UI. Поиск, сворачивание колонок, drag-and-drop, создание задач, комментарии и командные приглашения работают через единый versioned API FastAPI. Изменения доски публикуются через Redis Pub/Sub и доставляются подключённым WebSocket-клиентам с автоматическим reconnect/backoff.

Главный React-маршрут `/` — публичная landing page. Страницы `/login/`, `/register/`, `/dashboard/` и `/board/:id/` открываются через единый React-клиент.

## Проверка

Backend-тесты запускаются в изолированном контейнере с PostgreSQL и Redis:

```bash
docker compose run --rm --no-deps -e REDIS_URL=redis://redis:6379/15 --entrypoint pytest api -q
```

CI дополнительно выполняет цикл миграций `upgrade → downgrade → upgrade`, Ruff, mypy, ESLint, TypeScript typecheck/build, Playwright smoke-тест и сборку обоих Docker-образов. WebSocket получает одноразовый ticket через API, поэтому JWT не попадает в URL и proxy-логи.
