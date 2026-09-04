"""add unique usernames to users"""

from alembic import op


revision = "0004_usernames"
down_revision = "0003_invitation_codes"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(40)")
    op.execute("UPDATE users SET username = LOWER(SUBSTRING(SPLIT_PART(email, '@', 1), 1, 40)) WHERE username IS NULL")
    op.execute("UPDATE users u SET username = LEFT(u.username, 31) || '_' || u.id WHERE EXISTS (SELECT 1 FROM users other WHERE other.username = u.username AND other.id < u.id)")
    op.execute("ALTER TABLE users ALTER COLUMN username SET NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_users_username")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS username")
