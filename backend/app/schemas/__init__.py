from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.models import Priority


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    username: str
    email: str
    avatar_color: str


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str


class LabelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    color: str


class AssigneeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    avatar_color: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    priority: Priority
    due_date: date | None
    order: int
    assignee: AssigneeOut | None = None


class ColumnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    color: str
    order: int
    tasks: list[TaskOut]


class BoardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    workspace_id: int
    title: str
    description: str
    color: str
    is_favorite: bool
    is_archived: bool
    is_shared: bool = False
    can_edit: bool = False
    columns: list[ColumnOut]


class BoardSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    workspace_id: int
    title: str
    description: str
    color: str
    is_favorite: bool
    is_archived: bool
    is_shared: bool = False


class BoardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)


class BoardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=5000)
    color: str = Field(default="#8b5cf6", pattern=r"^#[0-9a-fA-F]{6}$")


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=5000)


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    text: str
    created_at: datetime
    actor: UserOut


class TaskCreate(BaseModel):
    column_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: Priority = Priority.medium
    due_date: date | None = None
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    priority: Priority | None = None
    due_date: date | None = None
    assignee_id: int | None = None
    column_id: int | None = None
    order: int | None = None


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    text: str
    created_at: datetime
    author: UserOut


class BoardMemberOut(UserOut):
    role: str = "member"


class BoardInviteCreate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=40)


class InvitationClaim(BaseModel):
    code: str = Field(min_length=4, max_length=12)


class BoardInvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    board_id: int
    board_title: str
    code: str
    invitee_id: int | None = None
    status: str
    created_at: datetime
    inviter: UserOut


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
    board_id: int | None = None
    invitation_id: int | None = None
    actor: UserOut | None = None
