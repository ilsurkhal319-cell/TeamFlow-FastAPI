from sqlalchemy.orm import Session

from app.domain.models import Activity


def record(db: Session, workspace_id: int, actor_id: int, text: str) -> Activity:
    activity = Activity(workspace_id=workspace_id, actor_id=actor_id, text=text)
    db.add(activity)
    return activity
