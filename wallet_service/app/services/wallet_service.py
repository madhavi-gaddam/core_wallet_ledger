import uuid
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, InsufficientFundsError, NotFoundError
from app.models.ledger_entry import TransactionType
from app.repositories.ledger_repository import LedgerRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.wallet import MoneyOperation, WalletCreate


class WalletService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.wallets = WalletRepository(db)
        self.ledger = LedgerRepository(db)

    def create_wallet(self, payload: WalletCreate):
        user = self.users.get_by_id(payload.user_id)
        if not user:
            raise NotFoundError("User not found.")

        if self.wallets.get_by_user_id(payload.user_id):
            raise ConflictError("User already has a wallet.")

        try:
            wallet = self.wallets.create(payload.user_id)
            self.db.commit()
            self.db.refresh(wallet)
            return wallet
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("User already has a wallet.") from exc

    def get_balance(self, wallet_id: uuid.UUID):
        wallet = self.wallets.get_by_id(wallet_id)
        if not wallet:
            raise NotFoundError("Wallet not found.")
        return wallet

    def credit(self, wallet_id: uuid.UUID, payload: MoneyOperation):
        return self._apply_transaction(
            wallet_id=wallet_id,
            transaction_type=TransactionType.CREDIT,
            amount=payload.amount,
            description=payload.description,
        )

    def debit(self, wallet_id: uuid.UUID, payload: MoneyOperation):
        return self._apply_transaction(
            wallet_id=wallet_id,
            transaction_type=TransactionType.DEBIT,
            amount=payload.amount,
            description=payload.description,
        )

    def get_transactions(self, wallet_id: uuid.UUID):
        wallet = self.wallets.get_by_id(wallet_id)
        if not wallet:
            raise NotFoundError("Wallet not found.")
        return self.ledger.list_by_wallet_id(wallet_id)

    def _apply_transaction(
        self,
        wallet_id: uuid.UUID,
        transaction_type: TransactionType,
        amount: Decimal,
        description: str | None,
    ):
        try:
            wallet = self.wallets.get_by_id_for_update(wallet_id)
            if not wallet:
                raise NotFoundError("Wallet not found.")

            if transaction_type == TransactionType.DEBIT and wallet.balance < amount:
                raise InsufficientFundsError("Insufficient wallet balance.")

            if transaction_type == TransactionType.CREDIT:
                wallet.balance += amount
            else:
                wallet.balance -= amount

            entry = self.ledger.create(
                wallet_id=wallet.id,
                transaction_type=transaction_type,
                amount=amount,
                balance_after_transaction=wallet.balance,
                description=description,
            )
            self.db.commit()
            self.db.refresh(wallet)
            self.db.refresh(entry)
            return wallet, entry
        except (NotFoundError, InsufficientFundsError):
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise

