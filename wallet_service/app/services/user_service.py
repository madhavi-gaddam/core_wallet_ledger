from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def create_user(self, payload: UserCreate):
        if self.users.get_by_email(payload.email):
            raise ConflictError("A user with this email already exists.")

        try:
            user = self.users.create(name=payload.name, email=str(payload.email))
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("A user with this email already exists.") from exc

