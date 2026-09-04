from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SQLEnum, ForeignKey, String, Text, Table, Column as SAColumn, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


board_members = Table(
    "board_members", Base.metadata,
    SAColumn("board_id", ForeignKey("boards.id", ondelete="CASCADE"), primary_key=True),
    SAColumn("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    avatar_color: Mapped[str] = mapped_column(String(7), default="#8b5cf6")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    workspaces: Mapped[list["WorkspaceMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    assigned_tasks: Mapped[list["Task"]] = relationship(back_populates="assignee", foreign_keys="Task.assignee_id")
    owned_workspaces: Mapped[list["Workspace"]] = relationship(foreign_keys="Workspace.owner_id", back_populates="owner")
    sent_invitations: Mapped[list["BoardInvitation"]] = relationship(foreign_keys="BoardInvitation.inviter_id", back_populates="inviter")
    received_invitations: Mapped[list["BoardInvitation"]] = relationship(foreign_keys="BoardInvitation.invitee_id", back_populates="invitee")
    notifications: Mapped[list["Notification"]] = relationship(foreign_keys="Notification.recipient_id", back_populates="recipient", cascade="all, delete-orphan")

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def get_full_name(self) -> str:
        return self.name

    @property
    def date_joined(self) -> datetime:
        return self.created_at

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def bio(self) -> str:
        return ""

    @property
    def phone(self) -> str:
        return ""

    @property
    def avatar(self):
        return None


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    owner: Mapped[User] = relationship(foreign_keys=[owner_id], back_populates="owned_workspaces")
    members: Mapped[list["WorkspaceMember"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    boards: Mapped[list["Board"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20), default="member")
    user: Mapped[User] = relationship(back_populates="workspaces")
    workspace: Mapped[Workspace] = relationship(back_populates="members")


class Board(Base):
    __tablename__ = "boards"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default="")
    color: Mapped[str] = mapped_column(String(7), default="#8b5cf6")
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    workspace: Mapped[Workspace] = relationship(back_populates="boards")
    columns: Mapped[list["Column"]] = relationship(back_populates="board", cascade="all, delete-orphan", order_by="Column.order")
    members: Mapped[list[User]] = relationship(secondary=board_members)
    invitations: Mapped[list["BoardInvitation"]] = relationship(back_populates="board", cascade="all, delete-orphan")

    @property
    def task_count(self) -> int:
        return sum(len(column.tasks) for column in self.columns)

    @property
    def created_by_id(self) -> int:
        return self.workspace.owner_id if self.workspace else self.workspace_id

    @property
    def tasks(self) -> list["Task"]:
        return [task for column in self.columns for task in column.tasks]

    @property
    def tasks_in_progress(self) -> int:
        return sum(1 for task in self.tasks if task.column.title.lower() in {"in progress", "в работе"})

    @property
    def overdue_tasks(self) -> int:
        from datetime import date
        return sum(1 for task in self.tasks if task.due_date and task.due_date < date.today())


class Column(Base):
    __tablename__ = "columns"
    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(60))
    order: Mapped[int] = mapped_column(default=0)
    color: Mapped[str] = mapped_column(String(7), default="#64748b")
    board: Mapped[Board] = relationship(back_populates="columns")
    tasks: Mapped[list["Task"]] = relationship(back_populates="column", cascade="all, delete-orphan", order_by="Task.order")


class Label(Base):
    __tablename__ = "labels"
    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(30))
    color: Mapped[str] = mapped_column(String(7), default="#64748b")


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    column_id: Mapped[int] = mapped_column(ForeignKey("columns.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[Priority] = mapped_column(SQLEnum(Priority), default=Priority.medium)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    column: Mapped[Column] = relationship(back_populates="tasks")
    assignee: Mapped[User | None] = relationship(back_populates="assigned_tasks", foreign_keys=[assignee_id])
    comments: Mapped[list["Comment"]] = relationship(back_populates="task", cascade="all, delete-orphan", order_by="Comment.created_at")

    @property
    def get_priority_display(self) -> str:
        return {Priority.low: "Low", Priority.medium: "Medium", Priority.high: "High"}.get(self.priority, "Medium")

    @property
    def get_priority_color(self) -> str:
        return {Priority.low: "green-400", Priority.medium: "yellow-400", Priority.high: "red-400"}.get(self.priority, "zinc-400")

    @property
    def board_name(self) -> str:
        return self.column.board.title if self.column and self.column.board else ""

    @property
    def profile_status(self) -> str:
        return "completed" if self.column and self.column.title.lower() in {"done", "готово"} else "active"

    @property
    def profile_status_label(self) -> str:
        return "Завершена" if self.profile_status == "completed" else "Активна"


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    task: Mapped[Task] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    actor: Mapped[User] = relationship()


class BoardInvitation(Base):
    __tablename__ = "board_invitations"
    __table_args__ = (UniqueConstraint("board_id", "invitee_id", name="uq_board_invitation_invitee"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    invitee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    board: Mapped[Board] = relationship(back_populates="invitations")
    inviter: Mapped[User] = relationship(foreign_keys=[inviter_id], back_populates="sent_invitations")
    invitee: Mapped[User] = relationship(foreign_keys=[invitee_id], back_populates="received_invitations")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="invitation", cascade="all, delete-orphan")

    @property
    def board_title(self) -> str:
        return self.board.title if self.board else "Доска"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    board_id: Mapped[int | None] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"), nullable=True)
    invitation_id: Mapped[int | None] = mapped_column(ForeignKey("board_invitations.id", ondelete="CASCADE"), nullable=True)
    kind: Mapped[str] = mapped_column(String(40), default="system")
    title: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(String(255))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    recipient: Mapped[User] = relationship(foreign_keys=[recipient_id], back_populates="notifications")
    actor: Mapped[User | None] = relationship(foreign_keys=[actor_id])
    board: Mapped[Board | None] = relationship(foreign_keys=[board_id])
    invitation: Mapped[BoardInvitation | None] = relationship(back_populates="notifications")
