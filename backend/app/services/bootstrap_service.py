from sqlalchemy.orm import Session

from app.domain.models import Board, Column, User, Workspace, WorkspaceMember


def create_default_workspace(db: Session, user: User) -> Workspace:
    workspace = Workspace(name="Основное", description="Ваше рабочее пространство", owner_id=user.id)
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
    board = Board(workspace_id=workspace.id, title="Моя первая доска", description="Организуйте задачи и проекты", color="#8b5cf6", is_favorite=True)
    db.add(board)
    db.flush()
    board.members.append(user)
    for index, (title, color) in enumerate((("Запланировано", "#64748b"), ("В работе", "#8b5cf6"), ("На проверке", "#f59e0b"), ("Готово", "#10b981"))):
        db.add(Column(board_id=board.id, title=title, order=index, color=color))
    return workspace
