"""
Bet routes for creating, retrieving, and managing user bets.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from database import get_db
from models import Bet, Selection, Fixture, User, BetStatus, SelectionStatus, BetType, FixtureStatus, BonusTier
from schemas import BetCreate, BetResponse, BetListResponse, SelectionCreate, SelectionResponse
from routes_auth import get_current_user

router = APIRouter(prefix="/api/bets", tags=["bets"])


# ===================================
# UTILITY FUNCTIONS
# ===================================

def calculate_bonus_percentage(selection_count: int, db: Session) -> int:
    """Calculate win bonus percentage based on selection count."""
    if selection_count < 2:
        return 0
    
    # Query bonus tiers and find the applicable one
    tier = db.query(BonusTier).filter(
        BonusTier.min_selections <= selection_count
    ).order_by(BonusTier.min_selections.desc()).first()
    
    return tier.bonus_percentage if tier else 0


def validate_selections(selections: List[SelectionCreate], db: Session) -> tuple:
    """
    Validate all selections exist and are from different fixtures.
    Returns (total_odds, fixture_ids) or raises exception.
    """
    if not selections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one selection is required"
        )
    
    total_odds = Decimal("1.0")
    fixture_ids = []
    
    for selection in selections:
        # Check fixture exists
        fixture = db.query(Fixture).filter(Fixture.id == selection.fixture_id).first()
        if not fixture:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fixture {selection.fixture_id} not found"
            )
        
        # Prevent duplicate selections from same fixture
        if selection.fixture_id in fixture_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate selection from fixture {selection.fixture_id}"
            )
        
        fixture_ids.append(selection.fixture_id)
        
        # Validate pick and odds
        if selection.pick not in ['win1', 'draw', 'win2']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid pick: {selection.pick}"
            )
        
        # Validate odds match fixture odds
        if selection.pick == 'win1':
            expected_odds = fixture.odds_win_home
        elif selection.pick == 'draw':
            if fixture.odds_draw is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Draw not available for fixture {selection.fixture_id}"
                )
            expected_odds = fixture.odds_draw
        else:  # win2
            expected_odds = fixture.odds_win_away
        
        # Check odds are close (within 0.05 tolerance for floating point)
        if abs(selection.odds - expected_odds) > Decimal("0.05"):
            print(f"[bets] Warning: Odds mismatch - Expected {expected_odds}, got {selection.odds}")
        
        total_odds *= selection.odds
    
    return total_odds, fixture_ids


# ===================================
# ROUTES
# ===================================

@router.post("", response_model=BetResponse)
def create_bet(
    bet_create: BetCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Create a new bet (single or multi-bet).
    
    Request body:
    - **bet_type**: 'single' or 'multi'
    - **stake**: Bet amount (must be positive)
    - **selections**: List of selections with fixture_id, pick, pick_label, and odds
    - **win_bonus_percentage**: Will be calculated if not provided
    
    Returns created bet with ID and potential win amount.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token, db)
    
    print(f"[bets] Create bet - User ID: {user.id}, Stake: {bet_create.stake}, Selections: {len(bet_create.selections)}")
    
    # Validate selections
    total_odds, fixture_ids = validate_selections(bet_create.selections, db)
    
    # Check user has sufficient balance
    if user.wallet_balance < bet_create.stake:
        print(f"[bets] Insufficient balance - User ID: {user.id}, Balance: {user.wallet_balance}, Stake: {bet_create.stake}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient wallet balance"
        )
    
    # Calculate win bonus
    bonus_percentage = calculate_bonus_percentage(len(bet_create.selections), db)
    
    # Calculate potential win
    potential_win = bet_create.stake * total_odds
    
    # Create bet
    bet = Bet(
        user_id=user.id,
        bet_type=bet_create.bet_type,
        status=BetStatus.PENDING,
        stake=bet_create.stake,
        total_odds=total_odds,
        potential_win=potential_win,
        win_bonus_percentage=bonus_percentage,
        created_at=datetime.utcnow()
    )
    
    db.add(bet)
    db.flush()  # Get bet ID without committing
    
    # Create selections
    for i, selection_create in enumerate(bet_create.selections):
        selection = Selection(
            bet_id=bet.id,
            fixture_id=selection_create.fixture_id,
            pick=selection_create.pick,
            pick_label=selection_create.pick_label,
            odds=selection_create.odds,
            status=SelectionStatus.PENDING,
            created_at=datetime.utcnow()
        )
        db.add(selection)
    
    # Deduct stake from user wallet
    user.wallet_balance -= bet_create.stake
    user.total_wagered += bet_create.stake
    
    db.commit()
    db.refresh(bet)
    
    print(f"[bets] Bet created - Bet ID: {bet.id}, Total Odds: {total_odds}, Potential Win: {potential_win}")
    
    return BetResponse.model_validate(bet)


@router.get("", response_model=BetListResponse)
def list_user_bets(
    status: Optional[str] = Query(None, description="Filter by status (pending, won, lost, void, partial)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get all bets for the current user.
    
    Query Parameters:
    - **status**: Filter by bet status
    - **page**: Page number (default: 1)
    - **per_page**: Results per page (default: 20)
    
    Returns paginated list of user's bets.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token, db)
    
    print(f"[bets] List user bets - User ID: {user.id}, Status: {status}, Page: {page}")
    
    query = db.query(Bet).filter(Bet.user_id == user.id)
    
    if status:
        try:
            status_enum = BetStatus(status.lower())
            query = query.filter(Bet.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join([s.value for s in BetStatus])}"
            )
    
    total = query.count()
    
    offset = (page - 1) * per_page
    bets = query.order_by(Bet.created_at.desc()).offset(offset).limit(per_page).all()
    
    print(f"[bets] Retrieved {len(bets)} bets (total: {total})")
    
    return BetListResponse(
        bets=[BetResponse.model_validate(b) for b in bets],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{bet_id}", response_model=BetResponse)
def get_bet(
    bet_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific bet by ID.
    
    Only the bet owner can view their bets.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token, db)
    
    print(f"[bets] Get bet - Bet ID: {bet_id}, User ID: {user.id}")
    
    bet = db.query(Bet).filter(Bet.id == bet_id).first()
    
    if not bet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bet not found"
        )
    
    # Verify ownership
    if bet.user_id != user.id:
        print(f"[bets] Unauthorized access - Bet ID: {bet_id}, Attempt by User ID: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this bet"
        )
    
    return bet


@router.get("/stats/summary")
def get_bet_stats(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get bet statistics for current user.
    
    Returns total bets, wins, losses, win rate, and total profit/loss.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token, db)
    
    print(f"[bets] Get bet stats - User ID: {user.id}")
    
    total_bets = db.query(Bet).filter(Bet.user_id == user.id).count()
    won_bets = db.query(Bet).filter(
        and_(Bet.user_id == user.id, Bet.status == BetStatus.WON)
    ).count()
    lost_bets = db.query(Bet).filter(
        and_(Bet.user_id == user.id, Bet.status == BetStatus.LOST)
    ).count()
    
    win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
    total_profit = user.total_won - user.total_wagered
    
    return {
        "total_bets": total_bets,
        "won_bets": won_bets,
        "lost_bets": lost_bets,
        "pending_bets": total_bets - won_bets - lost_bets,
        "win_rate": round(win_rate, 2),
        "total_wagered": user.total_wagered,
        "total_won": user.total_won,
        "profit_loss": total_profit
    }


# ===================================
# ADMIN/INTERNAL ROUTES (for bet settlement)
# ===================================

@router.post("/admin/settle/{bet_id}")
def settle_bet(
    bet_id: int,
    db: Session = Depends(get_db)
):
    """
    Settle a bet based on fixture results (admin/internal use only).
    
    Determines win/loss status and credits user wallet if won.
    This would typically be called by a background job when fixtures complete.
    """
    print(f"[bets] Settle bet - Bet ID: {bet_id}")
    
    bet = db.query(Bet).filter(Bet.id == bet_id).first()
    
    if not bet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bet not found"
        )
    
    if bet.status != BetStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bet already settled with status: {bet.status}"
        )
    
    # Get user
    user = db.query(User).filter(User.id == bet.user_id).first()
    
    # Check all selections and determine bet outcome
    all_won = True
    any_lost = False
    partial_win = False
    
    for selection in bet.selections:
        fixture = selection.fixture
        
        if fixture.status != FixtureStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fixture {fixture.id} not yet completed"
            )
        
        # Determine if selection won
        selection_won = False
        
        if fixture.result == 'cancelled':
            selection.status = SelectionStatus.VOID
        elif selection.pick == 'win1' and fixture.result == 'home':
            selection.status = SelectionStatus.WON
            selection_won = True
        elif selection.pick == 'draw' and fixture.result == 'draw':
            selection.status = SelectionStatus.WON
            selection_won = True
        elif selection.pick == 'win2' and fixture.result == 'away':
            selection.status = SelectionStatus.WON
            selection_won = True
        else:
            selection.status = SelectionStatus.LOST
            any_lost = True
        
        if not selection_won and selection.status != SelectionStatus.VOID:
            all_won = False
    
    # Determine bet outcome
    if all_won and not any_lost:
        bet.status = BetStatus.WON
        # Calculate winnings with bonus
        bonus_amount = (bet.potential_win * Decimal(bet.win_bonus_percentage)) / Decimal("100")
        bet.actual_win = bet.potential_win + bonus_amount
        bet.win_bonus_amount = bonus_amount
        
        # Credit user wallet
        user.wallet_balance += bet.actual_win
        user.total_won += bet.actual_win
        
        print(f"[bets] Bet WON - Bet ID: {bet_id}, Winnings: {bet.actual_win}, Bonus: {bonus_amount}")
    
    elif any_lost:
        bet.status = BetStatus.LOST
        bet.actual_win = Decimal("0.00")
        print(f"[bets] Bet LOST - Bet ID: {bet_id}")
    
    else:
        bet.status = BetStatus.VOID
        # Refund stake on void
        user.wallet_balance += bet.stake
        print(f"[bets] Bet VOID - Bet ID: {bet_id}, Refund: {bet.stake}")
    
    bet.settled_at = datetime.utcnow()
    
    db.commit()
    db.refresh(bet)
    
    print(f"[bets] Bet settled - Bet ID: {bet_id}, Status: {bet.status}")
    
    return BetResponse.model_validate(bet)
