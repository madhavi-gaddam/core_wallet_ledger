from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.core.exceptions import ConflictError
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def create_user(self, payload: UserCreate):
        if payload.email and self.users.get_by_email(str(payload.email)):
            raise ConflictError("A user with this email already exists.")

        if self.users.get_by_username(payload.username):
            raise ConflictError("A user with this username already exists.")

        try:
            user = self.users.create(
                username=payload.username,
                email=str(payload.email) if payload.email else None,
                hashed_password=hash_password(payload.password),
            )
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("A user with this email already exists.") from exc
