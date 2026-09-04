from contextlib import asynccontextmanager
import secrets

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.core.security import hash_password
from app.core.config import settings
from app.db.session import Base, SessionLocal, engine
from app.domain.models import Activity, Board, Column, Priority, Task, User, Workspace, WorkspaceMember
from app.api.v1.router import api_router
from app.realtime.routes import router as realtime_router
from app.core.logging import configure_logging
from app.services.bootstrap_service import create_default_workspace


DEMO_BOARD_TRANSLATIONS = {
    "Website redesign": ("Редизайн сайта", "Обновление маркетингового сайта"),
}
DEMO_TASK_TRANSLATIONS = {
    "Collect customer feedback": ("Собрать отзывы клиентов", "Изучить интервью за последний спринт"),
    "Prepare launch checklist": ("Подготовить чек-лист запуска", "Согласовать запуск с маркетингом и поддержкой"),
    "Design landing page": ("Спроектировать лендинг", "Завершить первый экран и блок с отзывами"),
    "Set up analytics": ("Настроить аналитику", "Добавить события регистрации и активации"),
    "Review mobile layouts": ("Проверить мобильные макеты", "Проверить адаптивность на iOS и Android"),
    "Define visual direction": ("Определить визуальный стиль", "Мудборд утверждён командой"),
}
DEMO_COLUMN_TRANSLATIONS = {"Backlog": "Запланировано", "In progress": "В работе", "Review": "На проверке", "Done": "Готово"}


def localize_demo_content(db: Session, user: User) -> None:
    boards = db.scalars(
        select(Board)
        .options(selectinload(Board.columns).selectinload(Column.tasks))
        .where(Board.workspace.has(owner_id=user.id))
    ).all()
    changed = False
    for board in boards:
        board_translation = DEMO_BOARD_TRANSLATIONS.get(board.title)
        if board_translation:
            board.title, board.description = board_translation
            changed = True
        for column in board.columns:
            if column.title in DEMO_COLUMN_TRANSLATIONS:
                column.title = DEMO_COLUMN_TRANSLATIONS[column.title]
                changed = True
            for task in column.tasks:
                task_translation = DEMO_TASK_TRANSLATIONS.get(task.title)
                if task_translation:
                    task.title, task.description = task_translation
                    changed = True
    if changed:
        db.commit()


def seed_demo() -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == "demo@teamflow.dev"))
        if existing:
            workspace = db.scalar(select(Workspace).where(Workspace.owner_id == existing.id).order_by(Workspace.id))
            if workspace and workspace.name == "Acme Studio":
                workspace.name = "Основное"
                db.commit()
            elif not workspace:
                create_default_workspace(db, existing)
                db.commit()
            localize_demo_content(db, existing)
            return
        user = User(name="Alex Morgan", username="alex", email="demo@teamflow.dev", password_hash=hash_password(secrets.token_urlsafe(32)), avatar_color="#8b5cf6")
        db.add(user)
        db.flush()
        workspace = Workspace(name="Основное", description="Product design and engineering", owner_id=user.id)
        db.add(workspace)
        db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
        board = Board(workspace_id=workspace.id, title="Редизайн сайта", description="Обновление маркетингового сайта", color="#8b5cf6", is_favorite=True)
        db.add(board)
        db.flush()
        board.members.append(user)
        columns = []
        for index, (title, color) in enumerate((("Запланировано", "#64748b"), ("В работе", "#8b5cf6"), ("На проверке", "#f59e0b"), ("Готово", "#10b981"))):
            column = Column(board_id=board.id, title=title, order=index, color=color)
            db.add(column)
            columns.append(column)
        db.flush()
        demo_tasks = [
            (columns[0], "Собрать отзывы клиентов", "Изучить интервью за последний спринт", Priority.medium),
            (columns[0], "Подготовить чек-лист запуска", "Согласовать запуск с маркетингом и поддержкой", Priority.low),
            (columns[1], "Спроектировать лендинг", "Завершить первый экран и блок с отзывами", Priority.high),
            (columns[1], "Настроить аналитику", "Добавить события регистрации и активации", Priority.medium),
            (columns[2], "Проверить мобильные макеты", "Проверить адаптивность на iOS и Android", Priority.medium),
            (columns[3], "Определить визуальный стиль", "Мудборд утверждён командой", Priority.low),
        ]
        for order, (column, title, description, priority) in enumerate(demo_tasks):
            db.add(Task(column_id=column.id, title=title, description=description, priority=priority, order=order, assignee_id=user.id))
        db.add(Activity(workspace_id=workspace.id, actor_id=user.id, text="Alex создал доску «Редизайн сайта»"))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    if settings.environment.lower() != "production":
        Base.metadata.create_all(bind=engine)
    if settings.seed_demo:
        seed_demo()
    yield


app = FastAPI(title="TeamFlow API", version="1.0.0", description="Team collaboration and Kanban workspace API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(api_router, prefix="/api/v1")
app.include_router(realtime_router)


@app.get("/health", tags=["system"])
def health() -> dict:
    checks = {"database": "ok", "redis": "ok"}
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "unavailable"
    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
        client.close()
    except Exception:
        checks["redis"] = "unavailable"
    if any(value != "ok" for value in checks.values()):
        raise HTTPException(status_code=503, detail={"status": "degraded", "checks": checks})
    return {"status": "ok"}
