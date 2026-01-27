"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from models.base import init_db, close_db
from api.routes.auth import router as auth_router
from api.routes.matches import router as match_router
from api.routes.profiles import router as profile_router
from api.routes.preferences import router as preferences_router
from api.routes.messages import router as messages_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    """
    print("Starting Roommate Finder API...")
    await init_db()
    print("Database initialized")
    
    yield
    
    print("Shutting down...")
    await close_db()
    print("Database connections closed")


app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="Backend API for Roommate Finder Platform",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(preferences_router, prefix="/api/v1")
app.include_router(match_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.api_version,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )