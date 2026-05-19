"""
Authentication routes for user registration, login, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from decimal import Decimal

from database import get_db
from models import User
from schemas import UserCreate, UserLogin, UserResponse, SuccessResponse

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Change this!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ===================================
# UTILITY FUNCTIONS
# ===================================

def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str, db: Session = Depends(get_db)) -> User:
    """Extract and validate JWT token, return current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    return user


# ===================================
# ROUTES
# ===================================

@router.post("/register", response_model=UserResponse)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **username**: Unique username (3-50 chars)
    - **email**: Valid email address
    - **password**: Password (min 8 chars)
    
    Returns the created user.
    """
    print(f"[auth] Register attempt - Username: {user_create.username}, Email: {user_create.email}")
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_create.email) | (User.username == user_create.username)
    ).first()
    
    if existing_user:
        print(f"[auth] Registration failed - User already exists: {user_create.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_create.password)
    new_user = User(
        username=user_create.username,
        email=user_create.email,
        password_hash=hashed_password,
        wallet_balance=Decimal("0.00"),
        total_wagered=Decimal("0.00"),
        total_won=Decimal("0.00"),
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    print(f"[auth] User registered successfully - ID: {new_user.id}, Username: {new_user.username}")
    return new_user


@router.post("/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    User login endpoint.
    
    Returns access token and user info.
    """
    print(f"[auth] Login attempt - Email: {user_login.email}")
    
    # Find user by email
    user = db.query(User).filter(User.email == user_login.email).first()
    
    if not user or not verify_password(user_login.password, user.password_hash):
        print(f"[auth] Login failed - Invalid credentials: {user_login.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        print(f"[auth] Login failed - Account inactive: {user_login.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(user.id)
    
    print(f"[auth] Login successful - User ID: {user.id}, Email: {user.email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    token: str = Depends(lambda: ""),
    db: Session = Depends(get_db)
):
    """
    Get current user profile (requires Bearer token in Authorization header).
    
    Example: `Authorization: Bearer <token>`
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = get_current_user(token, db)
    print(f"[auth] Get current user - User ID: {user.id}")
    return user


@router.post("/logout")
def logout():
    """
    Logout endpoint (token invalidation handled by frontend).
    
    Frontend should discard the token after calling this.
    """
    print("[auth] User logged out")
    return {"message": "Logged out successfully"}
