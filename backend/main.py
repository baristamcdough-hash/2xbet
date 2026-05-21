"""
2xBet Backend - FastAPI Application Entry Point
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_tables

# Import route modules
from routes_auth import router as auth_router
from routes_fixtures import router as fixtures_router
from routes_bets import router as bets_router
from routes_wallet import router as wallet_router

# Initialize FastAPI app
app = FastAPI(
    title="2xBet API",
    description="Sports betting platform backend",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS middleware - environment-aware configuration
# In production, set ALLOWED_ORIGINS as a comma-separated env variable
# Example: ALLOWED_ORIGINS=https://2xbet.onrender.com,https://yourdomain.com
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Default: allow all origins (development and flexible production)
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
def startup():
    print("\n[startup] Initializing database...")
    create_tables()
    print("[startup] Database initialized\n")

# ===================================
# HEALTH CHECK
# ===================================

@app.get("/")
def home():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "project": "2xBet backend",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/api/health")
def health_check():
    """API health check endpoint."""
    return {
        "status": "ok",
        "service": "2xBet API",
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }


# ===================================
# ROUTE REGISTRATION
# ===================================

# Register route modules with app
app.include_router(auth_router)
app.include_router(fixtures_router)
app.include_router(bets_router)
app.include_router(wallet_router)


# ===================================
# ERROR HANDLERS
# ===================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    print(f"[error] Unhandled exception: {exc}")
    return {
        "success": False,
        "error": "An unexpected error occurred",
        "details": str(exc)
    }


# ===================================
# STARTUP LOGGING
# ===================================

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════╗
    ║     2xBet Backend API Server           ║
    ║     Starting on http://localhost:8000  ║
    ╚════════════════════════════════════════╝
    
    Routes:
    - Authentication:  /api/auth/*
    - Fixtures:        /api/fixtures/*
    - Bets:            /api/bets/*
    - Wallet:          /api/wallet/*
    
    Documentation:     http://localhost:8000/api/docs
    
    """)
    
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
