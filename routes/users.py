from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from core.security import get_password_hash
from models.user import User
from schemas.user import UserResponse, UserUpdate, UserPublicResponse
from utils.auth import get_current_admin, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])
logger = get_logger(__name__)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    logger.info(f"User profile accessed: {current_user.username}")
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user profile."""
    logger.info(f"Updating profile for user: {current_user.username}")

    # Update allowed fields
    if user_data.username is not None:
        current_user.username = user_data.username
    if user_data.email is not None:
        current_user.email = user_data.email
    if user_data.password is not None:
        current_user.password_hash = get_password_hash(user_data.password)

    db.commit()
    db.refresh(current_user)

    logger.info(f"Profile updated successfully: {current_user.username}")
    return current_user


@router.get("/public", response_model=List[UserPublicResponse])
def list_users_public(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all users (public info only - for any authenticated user)."""
    logger.info(f"User {current_user.username} listing public user info")
    users = db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    return users


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all users (admin only)."""
    logger.info(f"Admin {current_user.username} listing users")
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get user by ID (admin only)."""
    logger.info(f"Admin {current_user.username} fetching user ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        logger.warning(f"User not found: {user_id}")
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
    """Update user (admin only)."""
    logger.info(f"Admin {current_user.username} updating user ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update fields
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

    db.commit()
    db.refresh(user)

    logger.info(f"User updated successfully: {user.username}")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete user (admin only) - Soft delete by setting is_active to False."""
    logger.info(f"Admin {current_user.username} deactivating user ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Soft delete - set is_active to False
    user.is_active = False
    db.commit()

    logger.info(f"User deactivated successfully: {user.username}")
