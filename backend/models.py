"""
SQLAlchemy ORM models for 2xBet backend.
Defines schema for Users, Fixtures, Bets, and related entities.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum as SQLEnum,
    Numeric, Text, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from database import Base


# ===================================
# ENUMS
# ===================================

class BetStatus(str, Enum):
    """Status of a bet."""
    PENDING = "pending"          # Waiting for event outcome
    WON = "won"                  # All selections won
    LOST = "lost"                # One or more selections lost
    VOID = "void"                # Cancelled/refunded
    PARTIAL = "partial"          # Some selections won (for multi-bets)


class FixtureStatus(str, Enum):
    """Status of a fixture/match."""
    SCHEDULED = "scheduled"      # Not yet started
    LIVE = "live"                # Currently in progress
    COMPLETED = "completed"      # Match ended
    CANCELLED = "cancelled"      # Match cancelled/postponed


class SelectionStatus(str, Enum):
    """Status of individual selection within a bet."""
    PENDING = "pending"          # Outcome unknown
    WON = "won"                  # Selection won
    LOST = "lost"                # Selection lost
    VOID = "void"                # Cancelled/voided


class BetType(str, Enum):
    """Type of bet."""
    SINGLE = "single"            # Single bet (one selection)
    MULTI = "multi"              # Multiple selections (parlay)
    SYSTEM = "system"            # System bet (multiple combinations)


# ===================================
# USER & WALLET
# ===================================

class User(Base):
    """User account model with wallet management."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Wallet info
    wallet_balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_wagered = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_won = Column(Numeric(15, 2), default=0.00, nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    bets = relationship("Bet", back_populates="user", cascade="all, delete-orphan")
    wallet_transactions = relationship("WalletTransaction", back_populates="user", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('wallet_balance >= 0', name='check_wallet_balance_non_negative'),
        CheckConstraint('total_wagered >= 0', name='check_total_wagered_non_negative'),
        CheckConstraint('total_won >= 0', name='check_total_won_non_negative'),
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
    )


class WalletTransaction(Base):
    """Track all wallet transactions (deposits, withdrawals, bet settlements)."""
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # 'deposit', 'withdrawal', 'bet_placed', 'bet_won', 'bet_lost', 'refund'
    description = Column(Text, nullable=True)
    
    related_bet_id = Column(Integer, ForeignKey("bets.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="wallet_transactions")
    
    __table_args__ = (
        Index('idx_transaction_user_date', 'user_id', 'created_at'),
    )


# ===================================
# FIXTURES (MATCHES/EVENTS)
# ===================================

class Fixture(Base):
    """Sports fixture/match model with live odds."""
    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    sport = Column(String(50), nullable=False, index=True)  # 'soccer', 'basketball', etc.
    league = Column(String(100), nullable=False, index=True)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    
    # Odds (1X2 format for soccer, or win/loss for other sports)
    odds_win_home = Column(Numeric(6, 2), nullable=False)
    odds_draw = Column(Numeric(6, 2), nullable=True)  # NULL for non-soccer sports
    odds_win_away = Column(Numeric(6, 2), nullable=False)
    
    # Fixture timing and status
    scheduled_start = Column(DateTime, nullable=False, index=True)
    status = Column(SQLEnum(FixtureStatus), default=FixtureStatus.SCHEDULED, nullable=False, index=True)
    
    # Live score (when fixture is live or completed)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    
    # Result determination (if match is completed)
    result = Column(String(10), nullable=True)  # 'home', 'away', 'draw', 'cancelled'
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    selections = relationship("Selection", back_populates="fixture", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_fixture_sport_league', 'sport', 'league'),
        Index('idx_fixture_scheduled', 'scheduled_start'),
        Index('idx_fixture_status', 'status'),
    )


# ===================================
# BETS & SELECTIONS
# ===================================

class Bet(Base):
    """Bet model supporting single and multi-bets."""
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Bet details
    bet_type = Column(SQLEnum(BetType), default=BetType.SINGLE, nullable=False)
    status = Column(SQLEnum(BetStatus), default=BetStatus.PENDING, nullable=False, index=True)
    
    # Financial data
    stake = Column(Numeric(15, 2), nullable=False)
    total_odds = Column(Numeric(12, 4), nullable=False)  # Product of all selection odds
    potential_win = Column(Numeric(15, 2), nullable=False)  # stake * total_odds
    actual_win = Column(Numeric(15, 2), nullable=True)  # Filled when bet settles
    
    # Bonus
    win_bonus_percentage = Column(Integer, default=0, nullable=False)  # 0-25%
    win_bonus_amount = Column(Numeric(15, 2), nullable=True)  # Calculated at settlement
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    settled_at = Column(DateTime, nullable=True)  # When the bet's outcome is determined
    
    # Relationships
    user = relationship("User", back_populates="bets")
    selections = relationship("Selection", back_populates="bet", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_bet_user_created', 'user_id', 'created_at'),
        Index('idx_bet_status', 'status'),
        Index('idx_bet_user_status', 'user_id', 'status'),
    )


class Selection(Base):
    """Individual selection within a bet (one selection per bet for single bets, multiple for multi-bets)."""
    __tablename__ = "selections"

    id = Column(Integer, primary_key=True, index=True)
    bet_id = Column(Integer, ForeignKey("bets.id", ondelete="CASCADE"), nullable=False, index=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Selection details
    pick = Column(String(20), nullable=False)  # 'win1', 'draw', 'win2', etc.
    pick_label = Column(String(100), nullable=False)  # Human-readable label
    odds = Column(Numeric(6, 2), nullable=False)  # Odds at time of selection
    
    # Status
    status = Column(SQLEnum(SelectionStatus), default=SelectionStatus.PENDING, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    bet = relationship("Bet", back_populates="selections")
    fixture = relationship("Fixture", back_populates="selections")
    
    __table_args__ = (
        Index('idx_selection_bet', 'bet_id'),
        Index('idx_selection_fixture', 'fixture_id'),
    )


# ===================================
# BONUS TIERS
# ===================================

class BonusTier(Base):
    """Define win bonus percentages based on number of selections."""
    __tablename__ = "bonus_tiers"

    id = Column(Integer, primary_key=True, index=True)
    min_selections = Column(Integer, nullable=False, unique=True, index=True)
    bonus_percentage = Column(Integer, nullable=False)  # e.g., 5, 10, 15, 20, 25
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint('min_selections > 0', name='check_min_selections_positive'),
        CheckConstraint('bonus_percentage >= 0 AND bonus_percentage <= 100', name='check_bonus_percentage_range'),
    )
