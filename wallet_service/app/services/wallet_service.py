from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, InsufficientFundsError, NotFoundError
from app.models.ledger_entry import LedgerEntry, TransactionType
from app.models.wallet import Wallet
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

    def get_balance(self, wallet_id: int):
        wallet = self.wallets.get_by_id(wallet_id)
        if not wallet:
            raise NotFoundError("Wallet not found.")
        return wallet

    def credit(self, wallet_id: int, payload: MoneyOperation):
        return self._apply_transaction(
            wallet_id=wallet_id,
            transaction_type=TransactionType.CREDIT,
            amount=payload.amount,
            idempotency_key=payload.idempotency_key,
            description=payload.description,
        )

    def debit(self, wallet_id: int, payload: MoneyOperation):
        return self._apply_transaction(
            wallet_id=wallet_id,
            transaction_type=TransactionType.DEBIT,
            amount=payload.amount,
            idempotency_key=payload.idempotency_key,
            description=payload.description,
        )

    def get_transactions(self, wallet_id: int):
        wallet = self.wallets.get_by_id(wallet_id)
        if not wallet:
            raise NotFoundError("Wallet not found.")
        return self.ledger.list_by_wallet_id(wallet_id)

    def _apply_transaction(
        self,
        wallet_id: int,
        transaction_type: TransactionType,
        amount: Decimal,
        idempotency_key: str,
        description: str | None,
    ) -> tuple[Wallet, LedgerEntry]:
        try:
            with self.db.begin():
                # Row-level locking serializes all balance changes for this wallet
                # across threads, FastAPI workers, and separate app instances.
                wallet = self.wallets.get_by_id_for_update(wallet_id)
                if not wallet:
                    raise NotFoundError("Wallet not found.")

                existing_entry = self.ledger.get_by_idempotency_key(idempotency_key)
                if existing_entry:
                    self._validate_idempotent_replay(
                        existing_entry=existing_entry,
                        wallet_id=wallet_id,
                        transaction_type=transaction_type,
                        amount=amount,
                    )
                    return wallet, existing_entry

                if transaction_type == TransactionType.DEBIT and wallet.balance < amount:
                    raise InsufficientFundsError("Insufficient wallet balance.")

                balance_before = wallet.balance
                if transaction_type == TransactionType.CREDIT:
                    wallet.balance += amount
                else:
                    wallet.balance -= amount

                entry = self.ledger.create(
                    user_id=wallet.user_id,
                    wallet_id=wallet.id,
                    transaction_type=transaction_type,
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=wallet.balance,
                    idempotency_key=idempotency_key,
                    description=description,
                )

            self.db.refresh(wallet)
            self.db.refresh(entry)
            return wallet, entry
        except (NotFoundError, InsufficientFundsError, ConflictError):
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Idempotency key already exists.") from exc

    @staticmethod
    def _validate_idempotent_replay(
        existing_entry: LedgerEntry,
        wallet_id: int,
        transaction_type: TransactionType,
        amount: Decimal,
    ) -> None:
        if (
            existing_entry.wallet_id != wallet_id
            or existing_entry.transaction_type != transaction_type
            or existing_entry.amount != amount
        ):
            raise ConflictError(
                "Idempotency key was already used for a different transaction."
            )
