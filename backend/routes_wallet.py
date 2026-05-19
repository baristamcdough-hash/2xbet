"""
Wallet and transaction routes for user balance management and transaction history.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from database import get_db
from models import User, WalletTransaction, Bet, BetStatus
from schemas import UserWalletResponse, WalletTransactionResponse, WalletTransactionListResponse, SuccessResponse
from routes_auth import get_current_user

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


# ===================================
# UTILITY FUNCTIONS
# ===================================

def create_transaction(
    user_id: int,
    amount: Decimal,
    transaction_type: str,
    description: str = None,
    related_bet_id: int = None,
    db: Session = None
) -> WalletTransaction:
    """Create a wallet transaction record."""
    transaction = WalletTransaction(
        user_id=user_id,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        related_bet_id=related_bet_id,
        created_at=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


# ===================================
# ROUTES
# ===================================

@router.get("/balance", response_model=UserWalletResponse)
def get_wallet_balance(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get current wallet balance and statistics for the authenticated user.
    
    Returns:
    - **balance**: Current available balance
    - **total_wagered**: Total amount staked on bets
    - **total_won**: Total amount won from bets
    - **win_rate**: Calculated win rate percentage
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token, db)
    
    print(f"[wallet] Get balance - User ID: {user.id}, Balance: {user.wallet_balance}")
    
    # Calculate win rate
    win_rate = None
    if user.total_wagered > 0:
        win_rate = (user.total_won / user.total_wagered) * 100
    
    return UserWalletResponse(
        user_id=user.id,
        balance=user.wallet_balance,
        total_wagered=user.total_wagered,
        total_won=user.total_won,
        win_rate=round(win_rate, 2) if win_rate else None
    )


@router.post("/deposit", response_model=SuccessResponse)
def deposit_funds(
    amount: Decimal = Query(..., gt=0, description="Amount to deposit (must be positive)"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Deposit funds to wallet (mock endpoint for testing).
    
    Query Parameters:
    - **amount**: Deposit amount (must be greater than 0)
    
    Note: In production, this would integrate with a real payment gateway.
    For now, deposits are simulated for testing purposes.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token, db)
    
    # Validate amount
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deposit amount must be greater than 0"
        )
    
    # Cap deposit for safety in mock mode
    if amount > Decimal("10000.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum deposit amount is 10,000"
        )
    
    print(f"[wallet] Deposit - User ID: {user.id}, Amount: {amount}")
    
    # Update wallet balance
    user.wallet_balance += amount
    
    # Create transaction record
    transaction = WalletTransaction(
        user_id=user.id,
        amount=amount,
        transaction_type="deposit",
        description=f"Mock deposit of {amount}",
        created_at=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    
    print(f"[wallet] Deposit successful - User ID: {user.id}, New Balance: {user.wallet_balance}")
    
    return SuccessResponse(
        success=True,
        message=f"Deposited {amount} successfully",
        data={
            "transaction_id": transaction.id,
            "amount": str(amount),
            "new_balance": str(user.wallet_balance),
            "timestamp": transaction.created_at.isoformat()
        }
    )


@router.post("/withdraw", response_model=SuccessResponse)
def withdraw_funds(
    amount: Decimal = Query(..., gt=0, description="Amount to withdraw (must be positive)"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Withdraw funds from wallet (mock endpoint for testing).
    
    Query Parameters:
    - **amount**: Withdrawal amount (must be positive and not exceed balance)
    
    Note: In production, this would integrate with a real payment gateway.
    For now, withdrawals are simulated for testing purposes.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token, db)
    
    # Validate amount
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal amount must be greater than 0"
        )
    
    # Check sufficient balance
    if user.wallet_balance < amount:
        print(f"[wallet] Insufficient funds - User ID: {user.id}, Balance: {user.wallet_balance}, Requested: {amount}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient funds. Available balance: {user.wallet_balance}"
        )
    
    # Cap withdrawal for safety in mock mode
    if amount > Decimal("10000.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum withdrawal amount is 10,000"
        )
    
    print(f"[wallet] Withdrawal - User ID: {user.id}, Amount: {amount}")
    
    # Update wallet balance
    user.wallet_balance -= amount
    
    # Create transaction record
    transaction = WalletTransaction(
        user_id=user.id,
        amount=amount,
        transaction_type="withdrawal",
        description=f"Mock withdrawal of {amount}",
        created_at=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    
    print(f"[wallet] Withdrawal successful - User ID: {user.id}, New Balance: {user.wallet_balance}")
    
    return SuccessResponse(
        success=True,
        message=f"Withdrew {amount} successfully",
        data={
            "transaction_id": transaction.id,
            "amount": str(amount),
            "new_balance": str(user.wallet_balance),
            "timestamp": transaction.created_at.isoformat()
        }
    )


@router.get("/transactions", response_model=WalletTransactionListResponse)
def get_transaction_history(
    transaction_type: Optional[str] = Query(None, description="Filter by type (deposit, withdrawal, bet_placed, bet_won, bet_lost, refund)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get transaction history for the authenticated user.
    
    Query Parameters:
    - **transaction_type**: Filter by transaction type
    - **page**: Page number (default: 1)
    - **per_page**: Results per page (default: 20, max: 100)
    
    Returns paginated list of transactions ordered by most recent first.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token, db)
    
    print(f"[wallet] Get transactions - User ID: {user.id}, Type: {transaction_type}, Page: {page}")
    
    query = db.query(WalletTransaction).filter(WalletTransaction.user_id == user.id)
    
    # Apply type filter if provided
    if transaction_type:
        valid_types = ['deposit', 'withdrawal', 'bet_placed', 'bet_won', 'bet_lost', 'refund']
        if transaction_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid transaction type. Must be one of: {', '.join(valid_types)}"
            )
        query = query.filter(WalletTransaction.transaction_type == transaction_type)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering (newest first)
    offset = (page - 1) * per_page
    transactions = query.order_by(WalletTransaction.created_at.desc()).offset(offset).limit(per_page).all()
    
    print(f"[wallet] Retrieved {len(transactions)} transactions (total: {total})")
    
    return WalletTransactionListResponse(
        transactions=[WalletTransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/transactions/{transaction_id}", response_model=WalletTransactionResponse)
def get_transaction_details(
    transaction_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific transaction by ID.
    
    Only the transaction owner can view their transactions.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token, db)
    
    print(f"[wallet] Get transaction - Transaction ID: {transaction_id}, User ID: {user.id}")
    
    transaction = db.query(WalletTransaction).filter(WalletTransaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Verify ownership
    if transaction.user_id != user.id:
        print(f"[wallet] Unauthorized access - Transaction ID: {transaction_id}, Attempt by User ID: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this transaction"
        )
    
    return transaction


@router.get("/summary")
def get_wallet_summary(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive wallet summary for the authenticated user.
    
    Includes:
    - Current balance
    - Total wagered
    - Total won
    - Win rate percentage
    - Profit/loss
    - Recent transactions count
    - Active bets count
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token, db)
    
    print(f"[wallet] Get wallet summary - User ID: {user.id}")
    
    # Count recent transactions (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_transactions = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user.id,
        WalletTransaction.created_at >= week_ago
    ).count()
    
    # Calculate win rate
    win_rate = None
    if user.total_wagered > 0:
        win_rate = (user.total_won / user.total_wagered) * 100
    
    profit_loss = user.total_won - user.total_wagered
    
    # Count active bets
    active_bets = db.query(Bet).filter(
        Bet.user_id == user.id,
        Bet.status == BetStatus.PENDING
    ).count()
    
    return {
        "balance": str(user.wallet_balance),
        "total_wagered": str(user.total_wagered),
        "total_won": str(user.total_won),
        "profit_loss": str(profit_loss),
        "win_rate": round(win_rate, 2) if win_rate else None,
        "recent_transactions_count": recent_transactions,
        "active_bets_count": active_bets,
        "updated_at": datetime.utcnow().isoformat()
    }


# ===================================
# ADMIN/INTERNAL ROUTES
# ===================================

@router.post("/admin/credit/{user_id}")
def admin_credit_wallet(
    user_id: int,
    amount: Decimal = Query(..., gt=0, description="Amount to credit"),
    reason: str = Query(..., description="Reason for credit"),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to credit a user's wallet (internal use only).
    
    Used for bonuses, refunds, and promotional credits.
    """
    print(f"[wallet] Admin credit - User ID: {user_id}, Amount: {amount}, Reason: {reason}")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update wallet
    user.wallet_balance += amount
    
    # Create transaction
    transaction = WalletTransaction(
        user_id=user_id,
        amount=amount,
        transaction_type="credit",
        description=f"Admin credit: {reason}",
        created_at=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    
    print(f"[wallet] Admin credit successful - User ID: {user_id}, New Balance: {user.wallet_balance}")
    
    return SuccessResponse(
        success=True,
        message=f"Credited {amount} to user {user_id}",
        data={
            "transaction_id": transaction.id,
            "user_id": user_id,
            "amount": str(amount),
            "reason": reason,
            "new_balance": str(user.wallet_balance)
        }
    )


@router.post("/admin/debit/{user_id}")
def admin_debit_wallet(
    user_id: int,
    amount: Decimal = Query(..., gt=0, description="Amount to debit"),
    reason: str = Query(..., description="Reason for debit"),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to debit a user's wallet (internal use only).
    
    Used for adjustments, chargebacks, and corrections.
    """
    print(f"[wallet] Admin debit - User ID: {user_id}, Amount: {amount}, Reason: {reason}")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check sufficient balance
    if user.wallet_balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient funds. Available: {user.wallet_balance}"
        )
    
    # Update wallet
    user.wallet_balance -= amount
    
    # Create transaction
    transaction = WalletTransaction(
        user_id=user_id,
        amount=amount,
        transaction_type="debit",
        description=f"Admin debit: {reason}",
        created_at=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    
    print(f"[wallet] Admin debit successful - User ID: {user_id}, New Balance: {user.wallet_balance}")
    
    return SuccessResponse(
        success=True,
        message=f"Debited {amount} from user {user_id}",
        data={
            "transaction_id": transaction.id,
            "user_id": user_id,
            "amount": str(amount),
            "reason": reason,
            "new_balance": str(user.wallet_balance)
        }
    )
