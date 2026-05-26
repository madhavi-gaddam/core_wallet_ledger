from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.ledger_entry import TransactionType


class LedgerEntryRead(BaseModel):
    id: int
    user_id: int
    wallet_id: int
    transaction_type: TransactionType
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    balance_after_transaction: Decimal
    idempotency_key: str | None
    description: str | None
    created_at: datetime | None

    model_config = {"from_attributes": True}
