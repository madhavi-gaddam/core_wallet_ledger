"""add phase 2 consistency to existing ledger schema

Revision ID: 20260526_0002
Revises: 20260525_0001
Create Date: 2026-05-26 00:02:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260526_0002"
down_revision: str | None = "20260525_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE ledger ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128)")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ledger_idempotency_key
        ON ledger (idempotency_key)
        WHERE idempotency_key IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_ledger_wallet_created_at
        ON ledger (wallet_id, created_at)
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_wallets_balance_non_negative'
            ) THEN
                ALTER TABLE wallets
                ADD CONSTRAINT ck_wallets_balance_non_negative CHECK (balance >= 0);
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_ledger_amount_positive'
            ) THEN
                ALTER TABLE ledger
                ADD CONSTRAINT ck_ledger_amount_positive CHECK (amount > 0);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE ledger DROP CONSTRAINT IF EXISTS ck_ledger_amount_positive")
    op.execute("ALTER TABLE wallets DROP CONSTRAINT IF EXISTS ck_wallets_balance_non_negative")
    op.execute("DROP INDEX IF EXISTS ix_ledger_wallet_created_at")
    op.execute("DROP INDEX IF EXISTS uq_ledger_idempotency_key")
    op.execute("ALTER TABLE ledger DROP COLUMN IF EXISTS idempotency_key")
