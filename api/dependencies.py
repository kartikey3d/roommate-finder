"""
FastAPI dependencies for authentication and common operations.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import get_db
from models.user import User
from services.auth_service import AuthService


security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user.
    
    Usage in route:
        current_user: User = Depends(get_current_user)
    """
    token = credentials.credentials
    user_id = auth_service.decode_token(token)
    user = await auth_service.get_current_user(db, user_id)
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active.
    """
    if current_user.account_state != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not active"
        )
    return current_user