from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.dependencies import current_user
from app.db.session import get_db
from app.domain.models import Board, User, Workspace
from app.schemas import BoardSummary

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("", response_model=list[BoardSummary])
def list_accessible_boards(archived: bool = False, user: User = Depends(current_user), db: Session = Depends(get_db)):
    boards = db.scalars(
        select(Board)
        .join(Board.workspace)
        .where(
            Board.is_archived.is_(archived),
            or_(Workspace.owner_id == user.id, Board.members.any(User.id == user.id)),
        )
        .order_by(Board.updated_at.desc(), Board.id.desc())
    ).all()
    return [
        BoardSummary.model_validate(board).model_copy(update={"is_shared": board.workspace.owner_id != user.id})
        for board in boards
    ]
