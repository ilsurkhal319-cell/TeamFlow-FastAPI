from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_user_id
from app.db.session import get_db
from app.domain.models import User, Workspace

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user_id = decode_user_id(token)
    user = db.get(User, user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def workspace_for_user(workspace_id: int, user: User, db: Session) -> Workspace:
    workspace = db.get(Workspace, workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace
