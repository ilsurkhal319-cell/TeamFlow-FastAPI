"""add short shareable invitation codes"""

from alembic import op


revision = "0003_invitation_codes"
down_revision = "0002_collaboration"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE board_invitations ALTER COLUMN invitee_id DROP NOT NULL")
    op.execute("ALTER TABLE board_invitations ADD COLUMN IF NOT EXISTS code VARCHAR(12)")
    op.execute("UPDATE board_invitations SET code = UPPER(SUBSTRING(MD5(RANDOM()::TEXT || id::TEXT), 1, 8)) WHERE code IS NULL")
    op.execute("ALTER TABLE board_invitations ALTER COLUMN code SET NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_board_invitations_code ON board_invitations (code)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_board_invitations_code")
    op.execute("ALTER TABLE board_invitations DROP COLUMN IF EXISTS code")
