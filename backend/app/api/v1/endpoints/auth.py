import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from redis import Redis

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.api.dependencies import current_user
from app.domain.models import Board, Column, Priority, Task, User
from app.services.bootstrap_service import create_default_workspace
from app.core.rate_limit import rate_limit
from app.core.config import settings
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db), _: None = Depends(rate_limit("register", 20, 60))):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    username = payload.username.strip().lower()
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status_code=409, detail="Username is already taken")
    user = User(name=payload.name.strip(), username=username, email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    create_default_workspace(db, user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db), _: None = Depends(rate_limit("login", 20, 60))):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return TokenOut(access_token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/demo", response_model=TokenOut)
def demo_login(db: Session = Depends(get_db)):
    """Issue a short-lived demo session when demo mode is explicitly enabled."""
    if not settings.demo_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Демо-режим отключён")
    suffix = secrets.token_hex(6)
    user = User(
        name="Alex Morgan",
        username=f"alex-demo-{suffix}",
        email=f"demo+{suffix}@teamflow.dev",
        password_hash=hash_password(secrets.token_urlsafe(32)),
        avatar_color="#8b5cf6",
    )
    db.add(user)
    db.flush()
    workspace = create_default_workspace(db, user)
    db.flush()
    board = db.scalar(select(Board).where(Board.workspace_id == workspace.id).order_by(Board.id))
    if board is None:
        raise HTTPException(status_code=500, detail="Не удалось создать демо-доску")
    columns = db.scalars(select(Column).where(Column.board_id == board.id).order_by(Column.order)).all()
    examples = [
        (columns[0], "Собрать отзывы клиентов", Priority.medium),
        (columns[0], "Подготовить чек-лист запуска", Priority.low),
        (columns[1], "Спроектировать лендинг", Priority.high),
        (columns[2], "Проверить макеты", Priority.medium),
    ]
    for order, (column, title, priority) in enumerate(examples):
        db.add(Task(column_id=column.id, title=title, description="Демо-задача TeamFlow", priority=priority, order=order, assignee_id=user.id))
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id, expires_minutes=45), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.post("/ws-ticket")
def websocket_ticket(user: User = Depends(current_user)):
    ticket = secrets.token_urlsafe(32)
    client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
    try:
        client.setex(f"teamflow:ws-ticket:{ticket}", 60, str(user.id))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Realtime-соединение временно недоступно") from exc
    finally:
        client.close()
    return {"ticket": ticket, "expires_in": 60}


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.name = payload.name.strip()
    db.commit()
    db.refresh(user)
    return user
