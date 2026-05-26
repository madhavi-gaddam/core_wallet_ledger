import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.ledger_entry import TransactionType


class LedgerEntryRead(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    transaction_type: TransactionType
    amount: Decimal
    balance_after_transaction: Decimal
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

