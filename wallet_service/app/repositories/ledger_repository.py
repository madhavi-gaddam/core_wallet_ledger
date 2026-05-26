import uuid
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.ledger_entry import LedgerEntry, TransactionType


class LedgerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        wallet_id: uuid.UUID,
        transaction_type: TransactionType,
        amount: Decimal,
        balance_after_transaction: Decimal,
        description: str | None,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            wallet_id=wallet_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_after_transaction=balance_after_transaction,
            description=description,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def list_by_wallet_id(self, wallet_id: uuid.UUID) -> list[LedgerEntry]:
        stmt = (
            select(LedgerEntry)
            .where(LedgerEntry.wallet_id == wallet_id)
            .order_by(desc(LedgerEntry.created_at))
        )
        return list(self.db.scalars(stmt).all())

