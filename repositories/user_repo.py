from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.user import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username_or_email(self, value: str) -> Optional[User]:
        return self.db.query(User).filter(
            or_(User.username == value, User.email == value)
        ).first()

    def exists_by_username(self, username: str) -> bool:
        return self.db.query(User).filter(User.username == username).first() is not None

    def exists_by_email(self, email: str) -> bool:
        return self.db.query(User).filter(User.email == email).first() is not None

    def exists_by_username_or_email(self, username: str, email: str) -> bool:
        return (
            self.db.query(User).filter(
                or_(User.username == username, User.email == email)
            ).first()
            is not None
        )

    def list_active(self, skip: int = 0, limit: int = 100) -> List[User]:
        return (
            self.db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
