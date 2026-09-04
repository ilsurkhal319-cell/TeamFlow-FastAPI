from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.dependencies import current_user
from app.db.session import get_db
from app.domain.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/search")
def search_users(q: str = "", user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = q.strip()
    if len(query) < 2:
        return {"users": []}
    pattern = f"%{query}%"
    users = db.scalars(
        select(User)
        .where(or_(User.name.ilike(pattern), User.username.ilike(pattern)), User.id != user.id)
        .order_by(User.username)
        .limit(10)
    ).all()
    return {"users": [{"id": item.id, "name": item.name, "username": item.username} for item in users]}
