"""Add invitations and notifications."""

import sqlalchemy as sa
from alembic import op

revision = "0002_collaboration"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "board_invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("board_id", sa.Integer(), sa.ForeignKey("boards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inviter_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invitee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("board_id", "invitee_id", name="uq_board_invitation_invitee"),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recipient_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("board_id", sa.Integer(), sa.ForeignKey("boards.id", ondelete="CASCADE"), nullable=True),
        sa.Column("invitation_id", sa.Integer(), sa.ForeignKey("board_invitations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String(length=40), nullable=False, server_default="system"),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_recipient_unread", "notifications", ["recipient_id", "is_read"])


def downgrade():
    op.drop_index("ix_notifications_recipient_unread", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("board_invitations")
