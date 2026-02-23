from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from core.config import settings
from core.logger import get_logger
from core.security import create_access_token, get_password_hash, verify_password
from enums import UserRole
from models.user import User
from repositories.user_repo import UserRepository
from schemas.user import UserCreate

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, user_data: UserCreate) -> User:
        logger.info(f"Attempting to register user: {user_data.username}")

        if self.user_repo.exists_by_username_or_email(user_data.username, user_data.email):
            logger.warning(f"Registration failed: User already exists - {user_data.username}")
            raise ValueError("Email or username already registered")

        hashed_password = get_password_hash(user_data.password)
        new_user = self.user_repo.create({
            "email": user_data.email,
            "username": user_data.username,
            "password_hash": hashed_password,
            "role": user_data.role,
        })
        self.user_repo.commit()
        self.user_repo.refresh(new_user)

        logger.info(f"User registered successfully: {new_user.username}")
        return new_user

    def login(self, username: str, password: str) -> dict:
        logger.info(f"Login attempt for user: {username}")

        user = self.user_repo.get_by_username(username)

        if not user or not verify_password(password, user.password_hash):
            logger.warning(f"Login failed: Invalid credentials for {username}")
            raise ValueError("Incorrect username or password")

        if not user.is_active:
            logger.warning(f"Login failed: Inactive user - {username}")
            raise ValueError("Inactive user")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role.value},
            expires_delta=access_token_expires,
        )

        logger.info(f"User logged in successfully: {user.username}")
        return {"access_token": access_token, "token_type": "bearer"}

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.user_repo.get_by_username(username)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)
