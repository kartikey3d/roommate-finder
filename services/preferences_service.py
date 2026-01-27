"""
Preferences service - manages user preferences CRUD operations.
Emits events for preference changes to trigger match recomputation.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.user import User, UserPreferences
from schemas.preferences import PreferencesCreate, PreferencesUpdate, PreferencesResponse
from events.definitions import publish_preferences_updated


class PreferencesService:
    """Service for managing user preferences."""
    
    async def create_preferences(
        self,
        db: AsyncSession,
        user_id: int,
        preferences_data: PreferencesCreate
    ) -> PreferencesResponse:
        """
        Create preferences for a user.
        
        Args:
            db: Database session
            user_id: ID of user creating preferences
            preferences_data: Preferences data to create
        
        Returns:
            Created preferences
        
        Raises:
            HTTPException: If user not found or preferences already exist
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
        
        # Check if preferences already exist
        result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Preferences already exist. Use update endpoint instead."
            )
        
        # Create preferences
        preferences = UserPreferences(
            user_id=user_id,
            budget_min=preferences_data.budget_min,
            budget_max=preferences_data.budget_max,
            cleanliness_level=preferences_data.cleanliness_level,
            sleep_schedule=preferences_data.sleep_schedule,
            smoking_ok=preferences_data.smoking_ok,
            drinking_ok=preferences_data.drinking_ok,
            pets_ok=preferences_data.pets_ok,
            guest_frequency=preferences_data.guest_frequency,
            is_student=preferences_data.is_student,
            is_working=preferences_data.is_working
        )
        
        db.add(preferences)
        await db.flush()
        await db.refresh(preferences)
        
        # Publish event for match recomputation
        publish_preferences_updated(
            user_id=user_id,
            changes=preferences_data.model_dump()
        )
        
        return PreferencesResponse.model_validate(preferences)
    
    async def get_preferences(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[PreferencesResponse]:
        """
        Get preferences for a user.
        
        Args:
            db: Database session
            user_id: ID of user
        
        Returns:
            User preferences or None if not found
        """
        result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            return None
        
        return PreferencesResponse.model_validate(preferences)
    
    async def get_preferences_or_404(
        self,
        db: AsyncSession,
        user_id: int
    ) -> PreferencesResponse:
        """
        Get preferences for a user or raise 404.
        
        Args:
            db: Database session
            user_id: ID of user
        
        Returns:
            User preferences
        
        Raises:
            HTTPException: If preferences not found
        """
        preferences = await self.get_preferences(db, user_id)
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preferences not found. Please create preferences first."
            )
        return preferences
    
    async def update_preferences(
        self,
        db: AsyncSession,
        user_id: int,
        update_data: PreferencesUpdate
    ) -> PreferencesResponse:
        """
        Update user preferences.
        
        Args:
            db: Database session
            user_id: ID of user
            update_data: Fields to update
        
        Returns:
            Updated preferences
        
        Raises:
            HTTPException: If preferences not found
        """
        # Get existing preferences
        result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preferences not found. Please create preferences first."
            )
        
        # Track changes for event
        changes = {}
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if value is not None:
                old_value = getattr(preferences, field)
                if old_value != value:
                    setattr(preferences, field, value)
                    changes[field] = {"old": old_value, "new": value}
        
        if not changes:
            # No actual changes
            return PreferencesResponse.model_validate(preferences)
        
        await db.flush()
        await db.refresh(preferences)
        
        # Publish event for match recomputation
        publish_preferences_updated(user_id=user_id, changes=changes)
        
        return PreferencesResponse.model_validate(preferences)
    
    async def delete_preferences(
        self,
        db: AsyncSession,
        user_id: int
    ) -> bool:
        """
        Delete user preferences.
        
        Args:
            db: Database session
            user_id: ID of user
        
        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            return False
        
        await db.delete(preferences)
        await db.flush()
        
        return True
    
    async def validate_budget_compatibility(
        self,
        db: AsyncSession,
        user_id: int,
        target_user_id: int
    ) -> dict:
        """
        Check budget compatibility between two users.
        
        Args:
            db: Database session
            user_id: First user ID
            target_user_id: Second user ID
        
        Returns:
            Dict with compatibility info
        """
        # Get both users' preferences
        user_prefs = await self.get_preferences(db, user_id)
        target_prefs = await self.get_preferences(db, target_user_id)
        
        if not user_prefs or not target_prefs:
            return {
                "compatible": False,
                "reason": "Missing preferences"
            }
        
        # Calculate overlap
        overlap_min = max(user_prefs.budget_min, target_prefs.budget_min)
        overlap_max = min(user_prefs.budget_max, target_prefs.budget_max)
        
        if overlap_max < overlap_min:
            return {
                "compatible": False,
                "reason": "No budget overlap",
                "user_range": (user_prefs.budget_min, user_prefs.budget_max),
                "target_range": (target_prefs.budget_min, target_prefs.budget_max)
            }
        
        overlap_range = overlap_max - overlap_min
        user_range = user_prefs.budget_max - user_prefs.budget_min
        target_range = target_prefs.budget_max - target_prefs.budget_min
        avg_range = (user_range + target_range) / 2
        
        overlap_percentage = (overlap_range / avg_range * 100) if avg_range > 0 else 100
        
        return {
            "compatible": True,
            "overlap_range": (overlap_min, overlap_max),
            "overlap_percentage": round(overlap_percentage, 2),
            "user_range": (user_prefs.budget_min, user_prefs.budget_max),
            "target_range": (target_prefs.budget_min, target_prefs.budget_max)
        }
    
    async def get_preference_summary(
        self,
        db: AsyncSession,
        user_id: int
    ) -> dict:
        """
        Get a summary of user preferences for quick display.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Summary dict with key preferences
        """
        preferences = await self.get_preferences(db, user_id)
        
        if not preferences:
            return {
                "has_preferences": False,
                "message": "No preferences set"
            }
        
        return {
            "has_preferences": True,
            "budget": f"${preferences.budget_min} - ${preferences.budget_max}",
            "cleanliness": preferences.cleanliness_level.value.replace("_", " ").title(),
            "sleep": preferences.sleep_schedule.value.replace("_", " ").title(),
            "lifestyle": {
                "smoking": "allowed" if preferences.smoking_ok else "not allowed",
                "pets": "allowed" if preferences.pets_ok else "not allowed",
                "drinking": "allowed" if preferences.drinking_ok else "not allowed"
            },
            "guests": preferences.guest_frequency.value.replace("_", " ").title(),
            "status": self._format_work_status(preferences.is_student, preferences.is_working)
        }
    
    @staticmethod
    def _format_work_status(is_student: bool, is_working: bool) -> str:
        """Format work status for display."""
        if is_student and is_working:
            return "Student & Working"
        elif is_student:
            return "Student"
        elif is_working:
            return "Working Professional"
        else:
            return "Other"