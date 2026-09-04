from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.api.dependencies import current_user, workspace_for_user
from app.domain.models import Activity, User, Workspace, WorkspaceMember
from app.schemas import ActivityOut, WorkspaceCreate, WorkspaceOut

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceOut])
def list_workspaces(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Workspace).where(Workspace.owner_id == user.id).order_by(Workspace.name)).all()


@router.post("", response_model=WorkspaceOut, status_code=201)
def create_workspace(payload: WorkspaceCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    workspace = Workspace(name=payload.name.strip(), description=payload.description.strip(), owner_id=user.id)
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
    db.commit()
    db.refresh(workspace)
    return workspace


@router.get("/{workspace_id}/activity", response_model=list[ActivityOut])
def list_activity(workspace_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    workspace_for_user(workspace_id, user, db)
    return db.scalars(
        select(Activity).options(selectinload(Activity.actor)).where(Activity.workspace_id == workspace_id).order_by(Activity.created_at.desc(), Activity.id.desc()).limit(50)
    ).all()
