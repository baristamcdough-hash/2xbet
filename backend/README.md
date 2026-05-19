# 2xBet Backend - FastAPI + SQLAlchemy + PostgreSQL

A production-ready sports betting backend with FastAPI, SQLAlchemy ORM, and PostgreSQL.

## Project Structure

```
backend/
├── database.py          # Database configuration and connection management
├── models.py            # SQLAlchemy ORM models (Users, Fixtures, Bets, etc.)
├── schemas.py           # Pydantic request/response validation models
├── init_db.py           # Database initialization script
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Database Schema

### Users Table
- User authentication and account info
- Wallet balance tracking
- Statistics (total_wagered, total_won)

### Wallet Transactions Table
- Audit trail for all wallet movements
- Links to related bets
- Transaction types: deposit, withdrawal, bet_placed, bet_won, bet_lost, refund

### Fixtures Table
- Sports matches/events
- Live odds (1X2 format for soccer, win/loss for others)
- Current scores and match status
- Indexed for fast queries by sport, league, status, scheduled time

### Bets Table
- User bets (single or multi-bet parlay)
- Bet status tracking (pending, won, lost, void, partial)
- Stake and potential win calculations
- Win bonus percentage and amount
- Timestamps for creation and settlement

### Selections Table
- Individual picks within a bet
- References fixture and specific pick (win1, draw, win2)
- Stores odds at time of selection (snapshot)
- Status tracking (pending, won, lost, void)

### Bonus Tiers Table
- Define win bonus percentages by number of selections
- Default: 2 selections = 5%, 3 = 10%, 4 = 15%, 5 = 20%, 6+ = 25%

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Database

**For Development (SQLite):**
```bash
# Default configuration uses SQLite at ./2xbet.db
python init_db.py
```

**For Production (PostgreSQL):**
```bash
# Set environment variable
export DATABASE_URL="postgresql://user:password@localhost:5432/2xbet"

# Create database
createdb 2xbet

# Initialize
python init_db.py
```

### 3. Initialize Database

```bash
python init_db.py
```

This will:
- Create all tables
- Seed bonus tiers
- Add sample fixtures for testing

## Key Design Decisions

### 1. Modular Structure
- **database.py** - Connection and session management
- **models.py** - ORM definitions only
- **schemas.py** - Request/response validation
- **init_db.py** - Initialization and seeding

### 2. Enum-Based Status Tracking
- Clear state machines for fixtures, bets, and selections
- Type-safe status transitions in future API logic

### 3. Decimal Fields for Financial Data
- Prevents float rounding errors
- Industry standard for currency operations

### 4. Snapshot Odds
- Selection odds stored at time of bet placement
- Protects against live odds fluctuations
- Allows odds history tracking

### 5. Win Bonus Calculation
- Tiered bonus based on selection count
- Easy to modify in BonusTier table
- Calculated and stored on bet settlement

### 6. Comprehensive Indexing
- Foreign keys indexed for fast joins
- Status and date fields indexed for filtering
- Composite indexes for common query patterns

## Next Steps

1. **Create main FastAPI app** (main.py)
2. **Implement API routes:**
   - Authentication (register, login, logout)
   - Fixtures (list, filter by sport/league/status)
   - Bets (create, list, settle)
   - Betslip (calculate, validate)
   - Wallet (get balance, history, deposit/withdraw)
3. **Implement business logic:**
   - Bet settlement logic
   - Win bonus calculation
   - Wallet transaction management
4. **Add WebSocket support** for live updates
5. **Add middleware** for auth, logging, error handling

## Database Constraints

- User wallet balance cannot be negative
- Bet stake must be positive
- Win bonus percentage between 0-100%
- Selection count must be positive for bonus tiers
- All timestamps in UTC

## Testing

```bash
# Run tests (to be implemented)
pytest tests/
```
