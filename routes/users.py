from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from models.user import User
from schemas.user import UserResponse, UserUpdate, UserPublicResponse
from services.user_service import UserService
from utils.auth import get_current_admin, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])
logger = get_logger(__name__)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    service = UserService(None)
    return service.get_current_user_profile(current_user)


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    return service.update_current_user_profile(current_user, user_data)


@router.get("/public", response_model=List[UserPublicResponse])
def list_users_public(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} listing public user info")
    service = UserService(db)
    return service.list_public(skip, limit)


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"Admin {current_user.username} listing users")
    service = UserService(db)
    return service.list_all(skip, limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"Admin {current_user.username} fetching user ID: {user_id}")
    service = UserService(db)
    user = service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"Admin {current_user.username} updating user ID: {user_id}")
    service = UserService(db)
    try:
        return service.update(user_id, user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"Admin {current_user.username} deactivating user ID: {user_id}")
    service = UserService(db)
    try:
        service.deactivate(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
