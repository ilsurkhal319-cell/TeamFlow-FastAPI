from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.api.dependencies import current_user
from app.domain.models import Column, Comment, Notification, Task, User
from app.schemas import CommentCreate, CommentOut, TaskCreate, TaskOut, TaskUpdate
from app.repositories.task_repository import get_with_assignee
from app.services.activity_service import record
from app.realtime.broker import publish_board_event

router = APIRouter(prefix="/tasks", tags=["tasks"])


def notify_board_members(db: Session, board, actor: User, *, kind: str, title: str, message: str) -> None:
    recipients = {member.id for member in board.members}
    recipients.add(board.workspace.owner_id)
    recipients.discard(actor.id)
    for recipient_id in recipients:
        db.add(Notification(recipient_id=recipient_id, actor_id=actor.id, board_id=board.id, kind=kind, title=title, message=message))


def task_with_assignee(task_id: int):
    return select(Task).options(selectinload(Task.assignee)).where(Task.id == task_id)


def authorized_task(task_id: int, user: User, db: Session) -> Task:
    task = db.scalar(select(Task).options(selectinload(Task.column).selectinload(Column.board)).where(Task.id == task_id))
    if not task or (task.column.board.workspace.owner_id != user.id and all(member.id != user.id for member in task.column.board.members)):
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def validate_assignee(board, assignee_id: int | None, db: Session) -> None:
    if assignee_id is None:
        return
    assignee = db.get(User, assignee_id)
    if not assignee or (board.workspace.owner_id != assignee.id and all(member.id != assignee.id for member in board.members)):
        raise HTTPException(status_code=400, detail="Исполнитель должен состоять в команде доски")


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    column = db.scalar(select(Column).options(selectinload(Column.board)).where(Column.id == payload.column_id))
    if not column or (column.board.workspace.owner_id != user.id and all(member.id != user.id for member in column.board.members)):
        raise HTTPException(status_code=404, detail="Column not found")
    validate_assignee(column.board, payload.assignee_id, db)
    max_order = db.scalar(select(Task.order).where(Task.column_id == column.id).order_by(Task.order.desc()).limit(1)) or 0
    task = Task(**payload.model_dump(), order=max_order + 1)
    db.add(task)
    notify_board_members(db, column.board, user, kind="task_created", title="Новая задача", message=f"{user.name} создал задачу «{task.title}»")
    record(db, column.board.workspace_id, user.id, f"{user.name} added {task.title}")
    db.commit()
    publish_board_event(column.board.id, {"type": "task.created", "board_id": column.board.id, "task_id": task.id})
    return get_with_assignee(db, task.id)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    task = authorized_task(task_id, user, db)
    changes = payload.model_dump(exclude_unset=True)
    moved_from = None
    moved_to = None
    if "column_id" in changes and changes["column_id"] != task.column_id:
        target_column = db.scalar(select(Column).where(Column.id == changes["column_id"]))
        if not target_column or target_column.board_id != task.column.board_id:
            raise HTTPException(status_code=400, detail="Задачу можно перемещать только внутри этой доски")
        moved_from = task.column.title
        moved_to = target_column.title
    if "assignee_id" in changes:
        validate_assignee(task.column.board, changes["assignee_id"], db)
    for key, value in changes.items():
        setattr(task, key, value)
    if moved_from is not None and moved_to is not None:
        notify_board_members(
            db,
            task.column.board,
            user,
            kind="task_moved",
            title="Задача перемещена",
            message=f"{user.name} переместил задачу «{task.title}» из «{moved_from}» в «{moved_to}»",
        )
    elif changes:
        notify_board_members(db, task.column.board, user, kind="task_updated", title="Задача обновлена", message=f"{user.name} обновил задачу «{task.title}»")
    db.commit()
    publish_board_event(task.column.board.id, {"type": "task.updated", "board_id": task.column.board.id, "task_id": task.id, "moved": moved_from is not None})
    return get_with_assignee(db, task_id)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    task = authorized_task(task_id, user, db)
    board = task.column.board
    notify_board_members(db, board, user, kind="task_deleted", title="Задача удалена", message=f"{user.name} удалил задачу «{task.title}»")
    db.delete(task)
    db.commit()
    publish_board_event(board.id, {"type": "task.deleted", "board_id": board.id, "task_id": task_id})


@router.get("/{task_id}/comments", response_model=list[CommentOut])
def list_comments(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorized_task(task_id, user, db)
    return db.scalars(select(Comment).options(selectinload(Comment.author)).where(Comment.task_id == task_id).order_by(Comment.created_at)).all()


@router.post("/{task_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(task_id: int, payload: CommentCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    task = authorized_task(task_id, user, db)
    comment = Comment(task_id=task.id, author_id=user.id, text=payload.text.strip())
    db.add(comment)
    notify_board_members(db, task.column.board, user, kind="task_commented", title="Новый комментарий", message=f"{user.name} прокомментировал задачу «{task.title}»")
    db.commit()
    publish_board_event(task.column.board.id, {"type": "task.comment.created", "board_id": task.column.board.id, "task_id": task.id, "comment_id": comment.id})
    return db.scalar(select(Comment).options(selectinload(Comment.author)).where(Comment.id == comment.id))
