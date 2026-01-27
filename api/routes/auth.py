"""
FastAPI routes for authentication.
Thin layer - business logic in AuthService.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import get_db
from models.user import User
from schemas.user import (
    UserSignupRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse
)
from services.auth_service import AuthService
from api.dependencies import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: UserSignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    **Creates:**
    - User account with hashed password
    - JWT access token (24-hour expiration)
    - Account in 'unverified' state
    
    **Requirements:**
    - Unique email address
    - Password minimum 8 characters
    - Name 1-100 characters
    - Age 18-100
    
    **Next Steps:**
    1. Create profile (/api/v1/profiles)
    2. Set preferences (/api/v1/preferences)
    3. Start matching!
    
    Returns:
        JWT access token and token type
    
    Raises:
        400: If email already registered
    """
    return await auth_service.signup(db, signup_data)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    **Authentication:**
    - Verifies email and password
    - Updates last login timestamp
    - Returns JWT access token
    
    **Token Usage:**
    - Include in Authorization header: `Bearer <token>`
    - Valid for 24 hours
    - No refresh tokens (re-login required)
    
    Returns:
        JWT access token and token type
    
    Raises:
        401: If credentials invalid
        403: If account suspended
    """
    return await auth_service.login(db, login_data.email, login_data.password)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user's information.
    
    **Returns:**
    - User account details
    - Account state
    - Profile (if created)
    - Preferences (if set)
    
    **Use Case:**
    - Verify authentication
    - Get user ID
    - Check account state
    - Load user dashboard
    
    Returns:
        Complete user object with nested profile and preferences
    
    Requires:
        Valid JWT token in Authorization header
    """
    return current_user


# Export router
__all__ = ["router"]