from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, hash_password, verify_password
from app.core.exceptions import ConflictError, UnauthorizedError
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: RegisterRequest):
        if self.users.get_by_username(payload.username):
            raise ConflictError("Username already exists.")

        try:
            user = self.users.create(
                username=payload.username,
                hashed_password=hash_password(payload.password),
            )
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Username already exists.") from exc

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.users.get_by_username(payload.username)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid username or password.")

        return TokenResponse(access_token=create_access_token(user.id))
