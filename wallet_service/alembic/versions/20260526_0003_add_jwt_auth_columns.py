"""add jwt auth columns

Revision ID: 20260526_0003
Revises: 20260526_0002
Create Date: 2026-05-26 00:03:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260526_0003"
down_revision: str | None = "20260526_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255)")
    op.execute("ALTER TABLE users ALTER COLUMN email DROP NOT NULL")


def downgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET email = username || '@local.invalid'
        WHERE email IS NULL
        """
    )
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS hashed_password")
    op.execute("ALTER TABLE users ALTER COLUMN email SET NOT NULL")
