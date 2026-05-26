import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class WalletCreate(BaseModel):
    user_id: uuid.UUID


class MoneyOperation(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    description: str | None = Field(default=None, max_length=255)


class WalletRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    balance: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class BalanceRead(BaseModel):
    wallet_id: uuid.UUID
    balance: Decimal


class WalletTransactionResponse(BaseModel):
    wallet_id: uuid.UUID
    balance: Decimal
    ledger_entry_id: uuid.UUID

