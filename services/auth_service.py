"""
Authentication service.
Handles user registration, login, and JWT token management.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.user import User, AccountState
from schemas.user import UserSignupRequest, TokenResponse
from config import get_settings


settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(user_id: int) -> str:
        """Create JWT access token."""
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
    
    @staticmethod
    def decode_token(token: str) -> int:
        """
        Decode JWT token and return user_id.
        Raises HTTPException if invalid.
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return int(user_id)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def signup(
        self,
        db: AsyncSession,
        signup_data: UserSignupRequest
    ) -> TokenResponse:
        """
        Register a new user.
        
        Returns:
            TokenResponse with access token
        
        Raises:
            HTTPException if email already exists
        """
        # Check if email exists
        result = await db.execute(
            select(User).where(User.email == signup_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        hashed_password = self.hash_password(signup_data.password)
        user = User(
            email=signup_data.email,
            hashed_password=hashed_password,
            account_state=AccountState.UNVERIFIED
        )
        
        db.add(user)
        await db.flush()
        await db.refresh(user)
        
        # Create access token
        access_token = self.create_access_token(user.id)
        
        return TokenResponse(access_token=access_token)
    
    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str
    ) -> TokenResponse:
        """
        Authenticate user and return token.
        
        Raises:
            HTTPException if credentials invalid
        """
        # Get user
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not self.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if suspended
        if user.account_state == AccountState.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account suspended"
            )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        await db.flush()
        
        # Create token
        access_token = self.create_access_token(user.id)
        
        return TokenResponse(access_token=access_token)
    
    async def get_current_user(
        self,
        db: AsyncSession,
        user_id: int
    ) -> User:
        """
        Get current user from database.
        
        Raises:
            HTTPException if user not found
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user