"""baseline existing wallet ledger tables

Revision ID: 20260525_0001
Revises:
Create Date: 2026-05-25 00:01:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260525_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the original integer-ID schema only when it is missing.

    Your existing database already has these tables, so this migration becomes
    a baseline marker there instead of creating duplicate Phase 1 tables.
    """

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) NOT NULL UNIQUE,
            email VARCHAR(120) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS wallets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            balance NUMERIC(15, 2) NOT NULL,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ledger (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            wallet_id INTEGER NOT NULL REFERENCES wallets(id),
            transaction_type VARCHAR(10) NOT NULL,
            amount NUMERIC(15, 2) NOT NULL,
            balance_before NUMERIC(15, 2) NOT NULL,
            balance_after NUMERIC(15, 2) NOT NULL,
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ledger")
    op.execute("DROP TABLE IF EXISTS wallets")
    op.execute("DROP TABLE IF EXISTS users")
