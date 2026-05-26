from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class WalletCreate(BaseModel):
    user_id: int


class MoneyOperation(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    idempotency_key: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=255)


class WalletRead(BaseModel):
    id: int
    user_id: int
    balance: Decimal
    created_at: datetime | None

    model_config = {"from_attributes": True}


class BalanceRead(BaseModel):
    wallet_id: int
    balance: Decimal


class WalletTransactionResponse(BaseModel):
    success: bool = True
    wallet_id: int
    balance: Decimal
    updated_balance: Decimal
    transaction_id: int
    ledger_entry_id: int
