from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.wallet import Wallet


class WalletRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int) -> Wallet:
        wallet = Wallet(user_id=user_id, balance=Decimal("0.00"))
        self.db.add(wallet)
        self.db.flush()
        return wallet

    def get_by_id(self, wallet_id: int) -> Wallet | None:
        return self.db.get(Wallet, wallet_id)

    def get_by_id_and_user_id(self, wallet_id: int, user_id: int) -> Wallet | None:
        stmt = select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
        return self.db.scalar(stmt)

    def get_by_user_id(self, user_id: int) -> Wallet | None:
        return self.db.scalar(select(Wallet).where(Wallet.user_id == user_id))

    def get_by_id_for_update(self, wallet_id: int) -> Wallet | None:
        stmt = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        return self.db.scalar(stmt)

    def get_by_id_and_user_id_for_update(
        self,
        wallet_id: int,
        user_id: int,
    ) -> Wallet | None:
        stmt = (
            select(Wallet)
            .where(Wallet.id == wallet_id, Wallet.user_id == user_id)
            .with_for_update()
        )
        return self.db.scalar(stmt)
