from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.ledger_entry import LedgerEntry, TransactionType


class LedgerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        wallet_id: int,
        transaction_type: TransactionType,
        amount: Decimal,
        balance_before: Decimal,
        balance_after: Decimal,
        idempotency_key: str,
        description: str | None,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            user_id=user_id,
            wallet_id=wallet_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            idempotency_key=idempotency_key,
            description=description,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def get_by_idempotency_key(self, idempotency_key: str) -> LedgerEntry | None:
        stmt = select(LedgerEntry).where(
            LedgerEntry.idempotency_key == idempotency_key
        )
        return self.db.scalar(stmt)

    def list_by_wallet_id(self, wallet_id: int) -> list[LedgerEntry]:
        stmt = (
            select(LedgerEntry)
            .where(LedgerEntry.wallet_id == wallet_id)
            .order_by(desc(LedgerEntry.created_at))
        )
        return list(self.db.scalars(stmt).all())
