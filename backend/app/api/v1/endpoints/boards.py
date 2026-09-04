from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.api.dependencies import current_user, workspace_for_user
from app.domain.models import Activity, Board, Column, Task, User
from app.schemas import BoardCreate, BoardOut, BoardSummary, BoardUpdate
from app.realtime.broker import publish_board_event

router = APIRouter(prefix="/workspaces/{workspace_id}/boards", tags=["boards"])


def board_query(board_id: int):
    return select(Board).options(selectinload(Board.columns).selectinload(Column.tasks).selectinload(Task.assignee)).where(Board.id == board_id)


@router.get("", response_model=list[BoardSummary])
def list_boards(workspace_id: int, archived: bool = False, user: User = Depends(current_user), db: Session = Depends(get_db)):
    workspace_for_user(workspace_id, user, db)
    return db.scalars(select(Board).where(Board.workspace_id == workspace_id, Board.is_archived.is_(archived)).order_by(Board.updated_at.desc())).all()


@router.get("/{board_id}", response_model=BoardOut)
def get_board(workspace_id: int, board_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    board = db.scalar(board_query(board_id))
    if not board or board.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Board not found")
    if board.workspace.owner_id != user.id and all(member.id != user.id for member in board.members):
        raise HTTPException(status_code=403, detail="You do not have access to this board")
    return BoardOut.model_validate(board).model_copy(update={"is_shared": board.workspace.owner_id != user.id, "can_edit": board.workspace.owner_id == user.id})


@router.patch("/{board_id}", response_model=BoardOut)
def update_board(workspace_id: int, board_id: int, payload: BoardUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    workspace_for_user(workspace_id, user, db)
    board = db.scalar(select(Board).where(Board.id == board_id, Board.workspace_id == workspace_id))
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    changes = payload.model_dump(exclude_unset=True)
    if "title" in changes:
        changes["title"] = changes["title"].strip()
        if not changes["title"]:
            raise HTTPException(status_code=422, detail="Название доски не может быть пустым")
    if "description" in changes and changes["description"] is not None:
        changes["description"] = changes["description"].strip()
    for key, value in changes.items():
        setattr(board, key, value)
    db.commit()
    publish_board_event(board.id, {"type": "board.updated", "board_id": board.id})
    db.refresh(board)
    updated = db.scalar(board_query(board.id))
    return BoardOut.model_validate(updated).model_copy(update={"is_shared": False, "can_edit": True})


@router.post("", response_model=BoardOut, status_code=201)
def create_board(workspace_id: int, payload: BoardCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    workspace_for_user(workspace_id, user, db)
    board = Board(workspace_id=workspace_id, title=payload.title.strip(), description=payload.description.strip(), color=payload.color)
    db.add(board)
    db.flush()
    board.members.append(user)
    for index, name in enumerate(("Запланировано", "В работе", "На проверке", "Готово")):
        db.add(Column(board_id=board.id, title=name, order=index, color=("#64748b", "#8b5cf6", "#f59e0b", "#10b981")[index]))
    db.add(Activity(workspace_id=workspace_id, actor_id=user.id, text=f"{user.name} created board {board.title}"))
    db.commit()
    publish_board_event(board.id, {"type": "board.created", "board_id": board.id})
    return db.scalar(board_query(board.id))


def owned_board(board_id: int, user: User, db: Session) -> Board:
    board = db.scalar(select(Board).where(Board.id == board_id, Board.workspace.has(owner_id=user.id)))
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@router.delete("/{board_id}", status_code=204)
def delete_board(workspace_id: int, board_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    workspace_for_user(workspace_id, user, db)
    board = owned_board(board_id, user, db)
    if board.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Board not found")
    db.delete(board)
    db.commit()


@router.post("/{board_id}/archive", response_model=BoardSummary)
def toggle_archive(workspace_id: int, board_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    workspace_for_user(workspace_id, user, db)
    board = owned_board(board_id, user, db)
    if board.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Board not found")
    board.is_archived = not board.is_archived
    db.commit()
    publish_board_event(board.id, {"type": "board.archived", "board_id": board.id, "is_archived": board.is_archived})
    return board


@router.post("/{board_id}/favorite", response_model=BoardSummary)
def toggle_favorite(workspace_id: int, board_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    workspace_for_user(workspace_id, user, db)
    board = owned_board(board_id, user, db)
    if board.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Board not found")
    board.is_favorite = not board.is_favorite
    db.commit()
    publish_board_event(board.id, {"type": "board.favorite", "board_id": board.id, "is_favorite": board.is_favorite})
    return board
