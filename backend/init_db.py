"""
Database initialization script.
Creates tables and seeds initial data (bonus tiers, sample fixtures).
"""

from database import create_tables, SessionLocal
from models import BonusTier, Fixture, FixtureStatus
from datetime import datetime, timedelta
from decimal import Decimal


def init_bonus_tiers(db):
    """Initialize bonus tier data."""
    print("[init_db] Creating bonus tiers...")
    
    tiers = [
        BonusTier(min_selections=1, bonus_percentage=0),
        BonusTier(min_selections=2, bonus_percentage=5),
        BonusTier(min_selections=3, bonus_percentage=10),
        BonusTier(min_selections=4, bonus_percentage=15),
        BonusTier(min_selections=5, bonus_percentage=20),
        BonusTier(min_selections=6, bonus_percentage=25),
    ]
    
    for tier in tiers:
        existing = db.query(BonusTier).filter_by(min_selections=tier.min_selections).first()
        if not existing:
            db.add(tier)
            print(f"  ✓ Bonus tier: {tier.min_selections} selections → {tier.bonus_percentage}%")
    
    db.commit()


def init_sample_fixtures(db):
    """Initialize sample fixtures for testing."""
    print("[init_db] Creating sample fixtures...")
    
    now = datetime.utcnow()
    
    fixtures = [
        Fixture(
            sport="soccer",
            league="Premier League",
            home_team="Manchester United",
            away_team="Liverpool",
            odds_win_home=Decimal("2.45"),
            odds_draw=Decimal("3.20"),
            odds_win_away=Decimal("2.80"),
            scheduled_start=now + timedelta(hours=2),
            status=FixtureStatus.SCHEDULED
        ),
        Fixture(
            sport="soccer",
            league="La Liga",
            home_team="Barcelona",
            away_team="Real Madrid",
            odds_win_home=Decimal("2.15"),
            odds_draw=Decimal("3.50"),
            odds_win_away=Decimal("3.40"),
            scheduled_start=now + timedelta(hours=5),
            status=FixtureStatus.SCHEDULED
        ),
        Fixture(
            sport="basketball",
            league="NBA",
            home_team="Lakers",
            away_team="Celtics",
            odds_win_home=Decimal("1.95"),
            odds_draw=None,
            odds_win_away=Decimal("1.85"),
            scheduled_start=now + timedelta(minutes=45),
            status=FixtureStatus.LIVE,
            home_score=78,
            away_score=82
        ),
        Fixture(
            sport="soccer",
            league="Premier League",
            home_team="Chelsea",
            away_team="Arsenal",
            odds_win_home=Decimal("2.30"),
            odds_draw=Decimal("3.10"),
            odds_win_away=Decimal("3.15"),
            scheduled_start=now + timedelta(hours=8),
            status=FixtureStatus.SCHEDULED
        ),
        Fixture(
            sport="soccer",
            league="Ligue 1",
            home_team="PSG",
            away_team="Monaco",
            odds_win_home=Decimal("1.65"),
            odds_draw=Decimal("3.80"),
            odds_win_away=Decimal("5.50"),
            scheduled_start=now + timedelta(hours=3, minutes=30),
            status=FixtureStatus.SCHEDULED
        ),
        Fixture(
            sport="basketball",
            league="NBA",
            home_team="Warriors",
            away_team="Nets",
            odds_win_home=Decimal("1.55"),
            odds_draw=None,
            odds_win_away=Decimal("2.35"),
            scheduled_start=now + timedelta(hours=6),
            status=FixtureStatus.SCHEDULED
        ),
    ]
    
    for fixture in fixtures:
        existing = db.query(Fixture).filter_by(
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            scheduled_start=fixture.scheduled_start
        ).first()
        if not existing:
            db.add(fixture)
            print(f"  ✓ Fixture: {fixture.home_team} vs {fixture.away_team} ({fixture.league})")
    
    db.commit()


def main():
    """Initialize the database."""
    print("\n========== 2xBet Database Initialization ==========\n")
    
    # Create tables
    print("[init_db] Creating database tables...")
    create_tables()
    print("  ✓ Tables created\n")
    
    # Get session
    db = SessionLocal()
    
    try:
        # Initialize bonus tiers
        init_bonus_tiers(db)
        print()
        
        # Initialize sample fixtures
        init_sample_fixtures(db)
        print()
        
        print("✅ Database initialization complete!\n")
    except Exception as e:
        print(f"❌ Error during initialization: {e}\n")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
