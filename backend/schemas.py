"""
Pydantic models for request/response validation and serialization.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from models import BetStatus, FixtureStatus, SelectionStatus, BetType


# ===================================
# USER SCHEMAS
# ===================================

class UserCreate(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response (public data only)."""
    id: int
    username: str
    email: str
    wallet_balance: Decimal
    total_wagered: Decimal
    total_won: Decimal
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserWalletResponse(BaseModel):
    """User wallet information."""
    user_id: int
    balance: Decimal
    total_wagered: Decimal
    total_won: Decimal
    win_rate: Optional[float] = None


# ===================================
# FIXTURE SCHEMAS
# ===================================

class FixtureResponse(BaseModel):
    """Fixture/match response."""
    id: int
    sport: str
    league: str
    home_team: str
    away_team: str
    odds_win_home: Decimal
    odds_draw: Optional[Decimal]
    odds_win_away: Decimal
    scheduled_start: datetime
    status: FixtureStatus
    home_score: Optional[int]
    away_score: Optional[int]
    result: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FixtureListResponse(BaseModel):
    """List of fixtures with pagination."""
    fixtures: List[FixtureResponse]
    total: int
    page: int
    per_page: int


# ===================================
# SELECTION SCHEMAS
# ===================================

class SelectionCreate(BaseModel):
    """Create a selection for a bet."""
    fixture_id: int
    pick: str  # 'win1', 'draw', 'win2'
    pick_label: str
    odds: Decimal


class SelectionResponse(BaseModel):
    """Selection in a bet."""
    id: int
    fixture_id: int
    pick: str
    pick_label: str
    odds: Decimal
    status: SelectionStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===================================
# BET SCHEMAS
# ===================================

class BetCreate(BaseModel):
    """Create a new bet."""
    bet_type: BetType = BetType.SINGLE
    stake: Decimal = Field(..., gt=0, decimal_places=2)
    selections: List[SelectionCreate]
    win_bonus_percentage: int = 0


class BetResponse(BaseModel):
    """Bet response."""
    id: int
    user_id: int
    bet_type: BetType
    status: BetStatus
    stake: Decimal
    total_odds: Decimal
    potential_win: Decimal
    actual_win: Optional[Decimal]
    win_bonus_percentage: int
    win_bonus_amount: Optional[Decimal]
    selections: List[SelectionResponse]
    created_at: datetime
    settled_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BetListResponse(BaseModel):
    """List of bets with pagination."""
    bets: List[BetResponse]
    total: int
    page: int
    per_page: int


# ===================================
# BETSLIP CALCULATION SCHEMAS
# ===================================

class BetslipCalculation(BaseModel):
    """Calculate betslip totals without submitting."""
    selections: List[SelectionCreate]
    stake: Decimal = Field(..., gt=0, decimal_places=2)


class BetslipCalculationResponse(BaseModel):
    """Betslip calculation result."""
    selection_count: int
    total_odds: Decimal
    stake: Decimal
    potential_win: Decimal
    win_bonus_percentage: int
    win_bonus_amount: Decimal
    total_with_bonus: Decimal


# ===================================
# WALLET TRANSACTION SCHEMAS
# ===================================

class WalletTransactionResponse(BaseModel):
    """Wallet transaction record."""
    id: int
    user_id: int
    amount: Decimal
    transaction_type: str
    description: Optional[str]
    related_bet_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class WalletTransactionListResponse(BaseModel):
    """List of transactions with pagination."""
    transactions: List[WalletTransactionResponse]
    total: int
    page: int
    per_page: int


# ===================================
# API RESPONSE SCHEMAS
# ===================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool
    error: str
    details: Optional[dict] = None
