"""
Profile service - manages user profile CRUD operations.
Emits events for profile changes to trigger match recomputation.
"""
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import date

from models.user import User, UserProfile
from schemas.user import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse
)
from events.definitions import publish_profile_updated


class ProfileService:
    """Service for managing user profiles."""
    
    async def create_profile(
        self,
        db: AsyncSession,
        user_id: int,
        profile_data: UserProfileCreate
    ) -> UserProfileResponse:
        """
        Create profile for a user.
        
        Args:
            db: Database session
            user_id: ID of user creating profile
            profile_data: Profile data to create
        
        Returns:
            Created profile
        
        Raises:
            HTTPException: If user not found or profile already exists
        """
        # Check if user exists
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if profile already exists
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile already exists. Use update endpoint instead."
            )
        
        # Validate move-in dates
        if profile_data.move_in_date_earliest and profile_data.move_in_date_latest:
            if profile_data.move_in_date_latest < profile_data.move_in_date_earliest:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="move_in_date_latest must be >= move_in_date_earliest"
                )
        
        # Create profile
        profile = UserProfile(
            user_id=user_id,
            name=profile_data.name,
            age=profile_data.age,
            gender=profile_data.gender,
            bio=profile_data.bio,
            city=profile_data.city,
            latitude=profile_data.latitude,
            longitude=profile_data.longitude,
            looking_for_short_term=profile_data.looking_for_short_term,
            looking_for_long_term=profile_data.looking_for_long_term,
            move_in_date_earliest=profile_data.move_in_date_earliest,
            move_in_date_latest=profile_data.move_in_date_latest,
            signals={}  # Initialize empty signals
        )
        
        db.add(profile)
        await db.flush()
        await db.refresh(profile)
        
        # Publish event for match computation
        publish_profile_updated(
            user_id=user_id,
            changes=profile_data.model_dump()
        )
        
        return UserProfileResponse.model_validate(profile)
    
    async def get_profile(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[UserProfileResponse]:
        """
        Get profile for a user.
        
        Args:
            db: Database session
            user_id: ID of user
        
        Returns:
            User profile or None if not found
        """
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return None
        
        return UserProfileResponse.model_validate(profile)
    
    async def get_profile_or_404(
        self,
        db: AsyncSession,
        user_id: int
    ) -> UserProfileResponse:
        """
        Get profile for a user or raise 404.
        
        Args:
            db: Database session
            user_id: ID of user
        
        Returns:
            User profile
        
        Raises:
            HTTPException: If profile not found
        """
        profile = await self.get_profile(db, user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create a profile first."
            )
        return profile
    
    async def update_profile(
        self,
        db: AsyncSession,
        user_id: int,
        update_data: UserProfileUpdate
    ) -> UserProfileResponse:
        """
        Update user profile.
        
        Args:
            db: Database session
            user_id: ID of user
            update_data: Fields to update
        
        Returns:
            Updated profile
        
        Raises:
            HTTPException: If profile not found or validation fails
        """
        # Get existing profile
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create a profile first."
            )
        
        # Track changes for event
        changes = {}
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Validate move-in dates if both are being updated
        if "move_in_date_earliest" in update_dict and "move_in_date_latest" in update_dict:
            earliest = update_dict["move_in_date_earliest"]
            latest = update_dict["move_in_date_latest"]
            if earliest and latest and latest < earliest:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="move_in_date_latest must be >= move_in_date_earliest"
                )
        
        # Apply updates
        for field, value in update_dict.items():
            if value is not None:
                old_value = getattr(profile, field)
                if old_value != value:
                    setattr(profile, field, value)
                    changes[field] = {"old": old_value, "new": value}
        
        if not changes:
            # No actual changes
            return UserProfileResponse.model_validate(profile)
        
        await db.flush()
        await db.refresh(profile)
        
        # Publish event for match recomputation
        publish_profile_updated(user_id=user_id, changes=changes)
        
        return UserProfileResponse.model_validate(profile)
    
    async def delete_profile(
        self,
        db: AsyncSession,
        user_id: int
    ) -> bool:
        """
        Delete user profile.
        
        Args:
            db: Database session
            user_id: ID of user
        
        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return False
        
        await db.delete(profile)
        await db.flush()
        
        return True
    
    async def search_profiles_by_location(
        self,
        db: AsyncSession,
        city: str,
        radius_km: Optional[float] = None,
        limit: int = 20
    ) -> List[UserProfileResponse]:
        """
        Search profiles by location.
        
        Args:
            db: Database session
            city: City to search in
            radius_km: Optional radius for proximity search
            limit: Maximum results
        
        Returns:
            List of matching profiles
        """
        # Basic city search (TODO: Add radius-based spatial search)
        result = await db.execute(
            select(UserProfile)
            .where(UserProfile.city.ilike(f"%{city}%"))
            .limit(limit)
        )
        profiles = result.scalars().all()
        
        return [UserProfileResponse.model_validate(p) for p in profiles]
    
    async def get_profiles_by_availability(
        self,
        db: AsyncSession,
        target_date: date,
        looking_for_short_term: Optional[bool] = None,
        looking_for_long_term: Optional[bool] = None,
        limit: int = 20
    ) -> List[UserProfileResponse]:
        """
        Get profiles available around a target date.
        
        Args:
            db: Database session
            target_date: Target move-in date
            looking_for_short_term: Filter by short-term preference
            looking_for_long_term: Filter by long-term preference
            limit: Maximum results
        
        Returns:
            List of available profiles
        """
        conditions = []
        
        # Date range filter
        conditions.append(
            and_(
                UserProfile.move_in_date_earliest <= target_date,
                UserProfile.move_in_date_latest >= target_date
            )
        )
        
        # Term preference filters
        if looking_for_short_term is not None:
            conditions.append(UserProfile.looking_for_short_term == looking_for_short_term)
        if looking_for_long_term is not None:
            conditions.append(UserProfile.looking_for_long_term == looking_for_long_term)
        
        result = await db.execute(
            select(UserProfile)
            .where(and_(*conditions))
            .limit(limit)
        )
        profiles = result.scalars().all()
        
        return [UserProfileResponse.model_validate(p) for p in profiles]
    
    async def update_signals(
        self,
        db: AsyncSession,
        user_id: int,
        signals: dict
    ) -> bool:
        """
        Update derived signals for a user profile.
        
        Signals are computed behavioral traits stored as JSONB.
        Examples: response_rate, ghosting_tendency, etc.
        
        Args:
            db: Database session
            user_id: User ID
            signals: Signals dict to merge
        
        Returns:
            True if updated, False if profile not found
        """
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return False
        
        # Merge new signals with existing
        current_signals = profile.signals or {}
        current_signals.update(signals)
        profile.signals = current_signals
        
        await db.flush()
        return True
    
    async def get_profile_completeness(
        self,
        db: AsyncSession,
        user_id: int
    ) -> dict:
        """
        Calculate profile completeness score.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Dict with completeness info
        """
        profile = await self.get_profile(db, user_id)
        
        if not profile:
            return {
                "score": 0,
                "missing_fields": ["all"],
                "message": "No profile created"
            }
        
        total_fields = 10
        filled_fields = 0
        missing_fields = []
        
        # Required fields
        if profile.name:
            filled_fields += 1
        else:
            missing_fields.append("name")
        
        if profile.age:
            filled_fields += 1
        else:
            missing_fields.append("age")
        
        if profile.city:
            filled_fields += 1
        else:
            missing_fields.append("city")
        
        # Optional but important fields
        if profile.gender:
            filled_fields += 1
        else:
            missing_fields.append("gender")
        
        if profile.bio:
            filled_fields += 1
        else:
            missing_fields.append("bio")
        
        if profile.move_in_date_earliest:
            filled_fields += 1
        else:
            missing_fields.append("move_in_date_earliest")
        
        if profile.move_in_date_latest:
            filled_fields += 1
        else:
            missing_fields.append("move_in_date_latest")
        
        # Location fields (counted as 1)
        if profile.latitude and profile.longitude:
            filled_fields += 2
        else:
            missing_fields.append("location")
        
        # Term preferences (counted as 1)
        if profile.looking_for_short_term or profile.looking_for_long_term:
            filled_fields += 1
        else:
            missing_fields.append("term_preference")
        
        score = int((filled_fields / total_fields) * 100)
        
        return {
            "score": score,
            "filled_fields": filled_fields,
            "total_fields": total_fields,
            "missing_fields": missing_fields,
            "is_complete": score >= 80
        }