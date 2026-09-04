from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.models import Task


def get_with_assignee(db: Session, task_id: int) -> Task | None:
    return db.scalar(select(Task).options(selectinload(Task.assignee)).where(Task.id == task_id))
