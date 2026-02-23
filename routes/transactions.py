from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from enums import TransactionStatus, TransactionType
from models.user import User
from schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate
from services.transaction_service import TransactionService
from utils.auth import get_current_operator_or_above, get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])
logger = get_logger(__name__)


def get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    skip: int = 0,
    limit: int = 100,
    transaction_type: Optional[TransactionType] = Query(None, alias="type"),
    transaction_status: Optional[TransactionStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} listing transactions")
    service = TransactionService(db)
    return service.list(skip, limit, transaction_type, transaction_status)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} fetching transaction ID: {transaction_id}")
    service = TransactionService(db)
    try:
        return service.get_by_id(transaction_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    request: Request,
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_operator_or_above),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} creating {transaction_data.transaction_type.value} transaction")
    service = TransactionService(db)
    client_ip = get_client_ip(request)
    try:
        return service.create(transaction_data, current_user, client_ip)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    request: Request,
    transaction_id: str,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_operator_or_above),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} updating transaction ID: {transaction_id}")
    service = TransactionService(db)
    client_ip = get_client_ip(request)
    try:
        return service.update(transaction_id, transaction_data, current_user, client_ip)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_transaction(
    request: Request,
    transaction_id: str,
    current_user: User = Depends(get_current_operator_or_above),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} cancelling transaction ID: {transaction_id}")
    service = TransactionService(db)
    client_ip = get_client_ip(request)
    try:
        service.cancel(transaction_id, current_user, client_ip)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
