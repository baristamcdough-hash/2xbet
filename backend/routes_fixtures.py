"""
Fixtures (matches/events) routes for retrieving live and upcoming matches with odds.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import Optional, List

from database import get_db
from models import Fixture, FixtureStatus
from schemas import FixtureResponse, FixtureListResponse

router = APIRouter(prefix="/api/fixtures", tags=["fixtures"])


# ===================================
# ROUTES
# ===================================

@router.get("", response_model=FixtureListResponse)
def list_fixtures(
    sport: Optional[str] = Query(None, description="Filter by sport (e.g., 'soccer', 'basketball')"),
    league: Optional[str] = Query(None, description="Filter by league"),
    status: Optional[str] = Query(None, description="Filter by status (scheduled, live, completed, cancelled)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List fixtures with optional filtering.
    
    Query Parameters:
    - **sport**: Filter by sport name
    - **league**: Filter by league name
    - **status**: Filter by fixture status
    - **page**: Page number (default: 1)
    - **per_page**: Results per page (default: 20, max: 100)
    
    Returns paginated list of fixtures.
    """
    print(f"[fixtures] List fixtures - Sport: {sport}, League: {league}, Status: {status}, Page: {page}")
    
    # Build query
    query = db.query(Fixture)
    
    # Apply filters
    if sport:
        query = query.filter(Fixture.sport.ilike(f"%{sport}%"))
    
    if league:
        query = query.filter(Fixture.league.ilike(f"%{league}%"))
    
    if status:
        try:
            status_enum = FixtureStatus(status.lower())
            query = query.filter(Fixture.status == status_enum)
        except ValueError:
            print(f"[fixtures] Invalid status: {status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join([s.value for s in FixtureStatus])}"
            )
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    fixtures = query.order_by(Fixture.scheduled_start.asc()).offset(offset).limit(per_page).all()
    
    print(f"[fixtures] Retrieved {len(fixtures)} fixtures (total: {total})")
    
    return FixtureListResponse(
        fixtures=[FixtureResponse.model_validate(f) for f in fixtures],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/live", response_model=FixtureListResponse)
def get_live_fixtures(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get all currently live fixtures.
    
    Returns paginated list of live matches only.
    """
    print(f"[fixtures] Get live fixtures - Page: {page}")
    
    query = db.query(Fixture).filter(Fixture.status == FixtureStatus.LIVE)
    total = query.count()
    
    offset = (page - 1) * per_page
    fixtures = query.order_by(Fixture.scheduled_start.asc()).offset(offset).limit(per_page).all()
    
    print(f"[fixtures] Retrieved {len(fixtures)} live fixtures (total: {total})")
    
    return FixtureListResponse(
        fixtures=[FixtureResponse.model_validate(f) for f in fixtures],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/upcoming", response_model=FixtureListResponse)
def get_upcoming_fixtures(
    hours_ahead: int = Query(24, ge=1, le=168, description="Look ahead hours (1-168)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get upcoming fixtures within specified hours.
    
    Query Parameters:
    - **hours_ahead**: How many hours ahead to look (default: 24, max: 168 for 1 week)
    
    Returns paginated list of scheduled matches.
    """
    print(f"[fixtures] Get upcoming fixtures - Hours: {hours_ahead}, Page: {page}")
    
    now = datetime.utcnow()
    future = datetime.utcnow() + timedelta(hours=hours_ahead)
    
    query = db.query(Fixture).filter(
        and_(
            Fixture.status == FixtureStatus.SCHEDULED,
            Fixture.scheduled_start >= now,
            Fixture.scheduled_start <= future
        )
    )
    total = query.count()
    
    offset = (page - 1) * per_page
    fixtures = query.order_by(Fixture.scheduled_start.asc()).offset(offset).limit(per_page).all()
    
    print(f"[fixtures] Retrieved {len(fixtures)} upcoming fixtures (total: {total})")
    
    return FixtureListResponse(
        fixtures=[FixtureResponse.model_validate(f) for f in fixtures],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{fixture_id}", response_model=FixtureResponse)
def get_fixture(fixture_id: int, db: Session = Depends(get_db)):
    """
    Get a single fixture by ID.
    
    Returns detailed fixture information including current odds and score.
    """
    print(f"[fixtures] Get fixture - ID: {fixture_id}")
    
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    
    if not fixture:
        print(f"[fixtures] Fixture not found - ID: {fixture_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixture not found"
        )
    
    return fixture


@router.get("/sport/{sport_name}", response_model=FixtureListResponse)
def get_fixtures_by_sport(
    sport_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get all fixtures for a specific sport.
    
    Examples: soccer, basketball, tennis, american-football, ice-hockey
    """
    print(f"[fixtures] Get fixtures by sport - Sport: {sport_name}, Page: {page}")
    
    query = db.query(Fixture).filter(Fixture.sport.ilike(f"%{sport_name}%"))
    total = query.count()
    
    offset = (page - 1) * per_page
    fixtures = query.order_by(Fixture.scheduled_start.asc()).offset(offset).limit(per_page).all()
    
    print(f"[fixtures] Retrieved {len(fixtures)} fixtures for sport '{sport_name}' (total: {total})")
    
    return FixtureListResponse(
        fixtures=[FixtureResponse.model_validate(f) for f in fixtures],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/league/{league_name}", response_model=FixtureListResponse)
def get_fixtures_by_league(
    league_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get all fixtures for a specific league.
    
    Examples: Premier League, La Liga, NBA, NFL, Champions League
    """
    print(f"[fixtures] Get fixtures by league - League: {league_name}, Page: {page}")
    
    query = db.query(Fixture).filter(Fixture.league.ilike(f"%{league_name}%"))
    total = query.count()
    
    offset = (page - 1) * per_page
    fixtures = query.order_by(Fixture.scheduled_start.asc()).offset(offset).limit(per_page).all()
    
    print(f"[fixtures] Retrieved {len(fixtures)} fixtures for league '{league_name}' (total: {total})")
    
    return FixtureListResponse(
        fixtures=[FixtureResponse.model_validate(f) for f in fixtures],
        total=total,
        page=page,
        per_page=per_page
    )


# ===================================
# ADMIN/INTERNAL ROUTES (for backend management)
# ===================================

@router.post("/admin/update-score/{fixture_id}")
def update_fixture_score(
    fixture_id: int,
    home_score: int,
    away_score: int,
    db: Session = Depends(get_db)
):
    """
    Update fixture score (admin/internal use only).
    
    In production, this would come from a live data feed or webhooks.
    """
    print(f"[fixtures] Update score - Fixture ID: {fixture_id}, Score: {home_score}-{away_score}")
    
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    
    if not fixture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixture not found"
        )
    
    fixture.home_score = home_score
    fixture.away_score = away_score
    
    if fixture.status == FixtureStatus.SCHEDULED:
        fixture.status = FixtureStatus.LIVE
    
    db.commit()
    db.refresh(fixture)
    
    print(f"[fixtures] Score updated - Fixture ID: {fixture_id}")
    
    return FixtureResponse.model_validate(fixture)


@router.post("/admin/complete/{fixture_id}")
def complete_fixture(
    fixture_id: int,
    result: str = Query(..., description="Result: 'home', 'away', 'draw', or 'cancelled'"),
    db: Session = Depends(get_db)
):
    """
    Mark fixture as completed (admin/internal use only).
    
    Triggers bet settlement logic.
    """
    print(f"[fixtures] Complete fixture - Fixture ID: {fixture_id}, Result: {result}")
    
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    
    if not fixture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixture not found"
        )
    
    if result not in ['home', 'away', 'draw', 'cancelled']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Result must be 'home', 'away', 'draw', or 'cancelled'"
        )
    
    fixture.status = FixtureStatus.COMPLETED
    fixture.result = result
    
    db.commit()
    db.refresh(fixture)
    
    print(f"[fixtures] Fixture completed - Fixture ID: {fixture_id}, Result: {result}")
    
    return FixtureResponse.model_validate(fixture)
