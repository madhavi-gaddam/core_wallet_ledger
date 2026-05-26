import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ledger_entry import LedgerEntryRead
from app.schemas.wallet import (
    BalanceRead,
    MoneyOperation,
    WalletCreate,
    WalletRead,
    WalletTransactionResponse,
)
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.post("", response_model=WalletRead, status_code=status.HTTP_201_CREATED)
def create_wallet(payload: WalletCreate, db: Session = Depends(get_db)):
    return WalletService(db).create_wallet(payload)


@router.post("/{wallet_id}/credit", response_model=WalletTransactionResponse)
def credit_wallet(
    wallet_id: uuid.UUID,
    payload: MoneyOperation,
    db: Session = Depends(get_db),
):
    wallet, entry = WalletService(db).credit(wallet_id, payload)
    return WalletTransactionResponse(
        wallet_id=wallet.id,
        balance=wallet.balance,
        ledger_entry_id=entry.id,
    )


@router.post("/{wallet_id}/debit", response_model=WalletTransactionResponse)
def debit_wallet(
    wallet_id: uuid.UUID,
    payload: MoneyOperation,
    db: Session = Depends(get_db),
):
    wallet, entry = WalletService(db).debit(wallet_id, payload)
    return WalletTransactionResponse(
        wallet_id=wallet.id,
        balance=wallet.balance,
        ledger_entry_id=entry.id,
    )


@router.get("/{wallet_id}/balance", response_model=BalanceRead)
def get_wallet_balance(wallet_id: uuid.UUID, db: Session = Depends(get_db)):
    wallet = WalletService(db).get_balance(wallet_id)
    return BalanceRead(wallet_id=wallet.id, balance=wallet.balance)


@router.get("/{wallet_id}/transactions", response_model=list[LedgerEntryRead])
def get_wallet_transactions(wallet_id: uuid.UUID, db: Session = Depends(get_db)):
    return WalletService(db).get_transactions(wallet_id)

