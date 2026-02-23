from typing import List, Optional

from sqlalchemy.orm import Session

from core.logger import get_logger
from core.security import get_password_hash
from models.user import User
from repositories.user_repo import UserRepository
from schemas.user import UserUpdate

logger = get_logger(__name__)


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)

    def get_current_user_profile(self, user: User) -> User:
        logger.info(f"User profile accessed: {user.username}")
        return user

    def update_current_user_profile(self, user: User, user_data: UserUpdate) -> User:
        logger.info(f"Updating profile for user: {user.username}")

        if user_data.username is not None:
            user.username = user_data.username
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.password is not None:
            user.password_hash = get_password_hash(user_data.password)

        self.user_repo.commit()
        self.user_repo.refresh(user)

        logger.info(f"Profile updated successfully: {user.username}")
        return user

    def list_public(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.user_repo.list_active(skip, limit)

    def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.user_repo.list(skip=skip, limit=limit)

    def update(self, user_id: str, user_data: UserUpdate) -> User:
        logger.info(f"Admin updating user ID: {user_id}")

        user = self.user_repo.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise ValueError("User not found")

        if user_data.email is not None:
            user.email = user_data.email
        if user_data.username is not None:
            user.username = user_data.username
        if user_data.role is not None:
            user.role = user_data.role
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.password is not None:
            user.password_hash = get_password_hash(user_data.password)

        self.user_repo.commit()
        self.user_repo.refresh(user)

        logger.info(f"User updated successfully: {user.username}")
        return user

    def deactivate(self, user_id: str) -> None:
        logger.info(f"Admin deactivating user ID: {user_id}")

        user = self.user_repo.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise ValueError("User not found")

        user.is_active = False
        self.user_repo.commit()

        logger.info(f"User deactivated successfully: {user.username}")
