from datetime import datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import current_user
from app.db.session import get_db
from app.domain.models import Board, BoardInvitation, User, Notification
from app.schemas import BoardInviteCreate, BoardInvitationOut, BoardMemberOut, InvitationClaim, NotificationOut
from app.core.rate_limit import rate_limit

router = APIRouter(tags=["collaboration"])


def board_for_user(board_id: int, user: User, db: Session) -> Board:
    board = db.scalar(
        select(Board)
        .options(selectinload(Board.members), selectinload(Board.workspace))
        .where(Board.id == board_id)
    )
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if board.workspace.owner_id != user.id and all(member.id != user.id for member in board.members):
        raise HTTPException(status_code=403, detail="You do not have access to this board")
    return board


def invitation_query(invitation_id: int):
    return (
        select(BoardInvitation)
        .options(selectinload(BoardInvitation.board), selectinload(BoardInvitation.inviter))
        .where(BoardInvitation.id == invitation_id)
    )


def invitation_query_by_code(code: str):
    return (
        select(BoardInvitation)
        .options(selectinload(BoardInvitation.board), selectinload(BoardInvitation.inviter))
        .where(BoardInvitation.code == code)
    )


@router.get("/boards/{board_id}/members")
def list_board_members(board_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    board = board_for_user(board_id, user, db)
    members = list(board.members)
    if all(member.id != board.workspace.owner_id for member in members):
        owner = db.get(User, board.workspace.owner_id)
        if owner:
            members.insert(0, owner)
    return {
        "owner_id": board.workspace.owner_id,
        "members": [BoardMemberOut.model_validate(member).model_dump() for member in members],
    }


@router.post("/boards/{board_id}/invitations", response_model=BoardInvitationOut, status_code=status.HTTP_201_CREATED)
def invite_to_board(
    board_id: int,
    payload: BoardInviteCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit("board-invite", 20, 60)),
):
    board = board_for_user(board_id, user, db)
    if board.workspace.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Только владелец может приглашать участников")
    lookup_username = payload.username.strip().lower() if payload.username else None
    lookup_email = str(payload.email).lower() if payload.email else None
    invitee = db.scalar(select(User).where(User.username == lookup_username)) if lookup_username else (db.scalar(select(User).where(User.email == lookup_email)) if lookup_email else None)
    if invitee and invitee.id == user.id:
        raise HTTPException(status_code=400, detail="Нельзя пригласить себя")
    if invitee and any(member.id == invitee.id for member in board.members):
        raise HTTPException(status_code=409, detail="Пользователь уже в команде доски")
    if (payload.email or payload.username) and not invitee:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if invitee:
        existing = db.scalar(select(BoardInvitation).where(BoardInvitation.board_id == board.id, BoardInvitation.invitee_id == invitee.id, BoardInvitation.status == "pending"))
        if existing:
            raise HTTPException(status_code=409, detail="Приглашение уже отправлено")

    code = None
    while not code or db.scalar(select(BoardInvitation.id).where(BoardInvitation.code == code)):
        code = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(8))
    invitation = BoardInvitation(board_id=board.id, inviter_id=user.id, invitee_id=invitee.id if invitee else None, code=code)
    db.add(invitation)
    db.flush()
    if invitee:
        db.add(Notification(
            recipient_id=invitee.id,
            actor_id=user.id,
            board_id=board.id,
            invitation_id=invitation.id,
            kind="board_invitation",
            title="Приглашение в команду",
            message=f"{user.name} приглашает вас в команду доски «{board.title}»",
        ))
    db.commit()
    return db.scalar(invitation_query(invitation.id))


@router.post("/invitations/claim", response_model=BoardInvitationOut)
def claim_invitation(payload: InvitationClaim, user: User = Depends(current_user), db: Session = Depends(get_db), _: None = Depends(rate_limit("invitation-claim", 10, 60))):
    invitation = db.scalar(invitation_query_by_code(payload.code.strip().upper()))
    if not invitation or invitation.status != "pending":
        raise HTTPException(status_code=404, detail="Код приглашения недействителен или уже использован")
    board = db.scalar(select(Board).options(selectinload(Board.members), selectinload(Board.workspace)).where(Board.id == invitation.board_id))
    if not board:
        raise HTTPException(status_code=404, detail="Доска для приглашения не найдена")
    if board.workspace.owner_id == user.id or any(member.id == user.id for member in board.members):
        raise HTTPException(status_code=409, detail="Вы уже участник этой доски")
    invitation.invitee_id = user.id
    invitation.status = "accepted"
    invitation.responded_at = datetime.utcnow()
    board.members.append(user)
    db.add(Notification(
        recipient_id=invitation.inviter_id,
        actor_id=user.id,
        board_id=board.id,
        invitation_id=invitation.id,
        kind="board_invitation_accepted",
        title="Приглашение принято",
        message=f"{user.name} присоединился к команде доски «{board.title}»",
    ))
    db.commit()
    return db.scalar(invitation_query(invitation.id))


@router.get("/invitations/{invitation_id}", response_model=BoardInvitationOut)
def get_invitation(invitation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    invitation = db.scalar(invitation_query(invitation_id))
    if not invitation or invitation.invitee_id != user.id:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return invitation


@router.post("/invitations/{invitation_id}/accept", response_model=BoardInvitationOut)
def accept_invitation(invitation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    invitation = db.scalar(invitation_query(invitation_id))
    if not invitation or invitation.invitee_id != user.id:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.status != "pending":
        raise HTTPException(status_code=409, detail="Приглашение уже обработано")

    board = db.scalar(select(Board).options(selectinload(Board.members), selectinload(Board.workspace)).where(Board.id == invitation.board_id))
    if not board:
        raise HTTPException(status_code=404, detail="Доска для приглашения не найдена")
    invitation.status = "accepted"
    invitation.responded_at = datetime.utcnow()
    for notification in db.scalars(select(Notification).where(Notification.invitation_id == invitation.id, Notification.recipient_id == user.id)).all():
        notification.is_read = True
    if all(member.id != user.id for member in board.members):
        board.members.append(user)
    db.add(Notification(
        recipient_id=invitation.inviter_id,
        actor_id=user.id,
        board_id=board.id,
        kind="board_invitation_accepted",
        title="Приглашение принято",
        message=f"{user.name} присоединился к команде доски «{board.title}»",
    ))
    db.commit()
    return db.scalar(invitation_query(invitation.id))


@router.post("/invitations/{invitation_id}/decline", response_model=BoardInvitationOut)
def decline_invitation(invitation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    invitation = db.scalar(invitation_query(invitation_id))
    if not invitation or invitation.invitee_id != user.id:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.status != "pending":
        raise HTTPException(status_code=409, detail="Приглашение уже обработано")
    invitation.status = "declined"
    invitation.responded_at = datetime.utcnow()
    for notification in db.scalars(select(Notification).where(Notification.invitation_id == invitation.id, Notification.recipient_id == user.id)).all():
        notification.is_read = True
    db.add(Notification(
        recipient_id=invitation.inviter_id,
        actor_id=user.id,
        board_id=invitation.board_id,
        kind="board_invitation_declined",
        title="Приглашение отклонено",
        message=f"{user.name} отклонил приглашение в команду доски «{invitation.board.title}»",
    ))
    db.commit()
    return db.scalar(invitation_query(invitation.id))


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Notification)
        .options(selectinload(Notification.actor))
        .where(Notification.recipient_id == user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(50)
    ).all()


@router.get("/notifications/unread-count")
def unread_notifications_count(user: User = Depends(current_user), db: Session = Depends(get_db)):
    from sqlalchemy import func
    return {"unread_count": db.scalar(select(func.count(Notification.id)).where(Notification.recipient_id == user.id, Notification.is_read.is_(False))) or 0}


@router.post("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_notifications_read(user: User = Depends(current_user), db: Session = Depends(get_db)):
    notifications = db.scalars(select(Notification).where(Notification.recipient_id == user.id, Notification.is_read.is_(False))).all()
    for notification in notifications:
        notification.is_read = True
    db.commit()


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_read(notification_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    notification = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.recipient_id == user.id))
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
