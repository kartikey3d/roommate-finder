"""
FastAPI routes for user profile management.
Thin layer - business logic in ProfileService.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from models.base import get_db
from models.user import User
from schemas.user import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse
)
from services.profile_service import ProfileService
from api.dependencies import get_current_user, get_current_active_user


router = APIRouter(prefix="/profiles", tags=["Profiles"])
profile_service = ProfileService()


@router.post("", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create profile for the current user.
    
    **Requirements:**
    - User must be authenticated and active
    - User must not already have a profile
    
    **Validation:**
    - Age must be 18-100
    - Latitude: -90 to 90
    - Longitude: -180 to 180
    - If both move-in dates provided, latest >= earliest
    - At least one of looking_for_short_term or looking_for_long_term must be true
    
    **Triggers:**
    - Emits `profile_updated` event
    - Triggers async match computation
    
    Returns:
        Created profile object
    """
    return await profile_service.create_profile(
        db=db,
        user_id=current_user.id,
        profile_data=profile_data
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's profile.
    
    Returns:
        User profile
    
    Raises:
        404: If profile not found
    """
    profile = await profile_service.get_profile(db, current_user.id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create a profile first."
        )
    
    return profile


@router.get("/me/completeness")
async def get_my_profile_completeness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get profile completeness score for current user.
    
    Returns profile completeness as a percentage with:
    - score: 0-100
    - filled_fields: count of completed fields
    - missing_fields: list of incomplete fields
    - is_complete: bool (score >= 80%)
    
    **Use Case:**
    - Guide users to complete their profile
    - Show progress indicator
    - Determine if user can access matching
    
    Returns:
        Completeness information dict
    """
    return await profile_service.get_profile_completeness(db, current_user.id)


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    update_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile.
    
    **Partial Updates:**
    - All fields are optional
    - Only provided fields will be updated
    - Omitted fields remain unchanged
    
    **Validation:**
    - Same validation rules as create
    - If both move-in dates provided, latest >= earliest
    
    **Triggers:**
    - Emits `profile_updated` event with changed fields
    - Triggers async match recomputation
    
    Returns:
        Updated profile object
    
    Raises:
        404: If profile not found
        400: If validation fails
    """
    return await profile_service.update_profile(
        db=db,
        user_id=current_user.id,
        update_data=update_data
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete current user's profile.
    
    **Warning:**
    - This action cannot be undone
    - User will not appear in matches until profile is recreated
    - All cached matches will be invalidated
    - Preferences will remain but won't be used
    
    Returns:
        204 No Content on success
    
    Raises:
        404: If profile not found
    """
    deleted = await profile_service.delete_profile(db, current_user.id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )


@router.get("/search/location", response_model=list[UserProfileResponse])
async def search_profiles_by_location(
    city: str = Query(..., min_length=1, description="City name to search"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search profiles by location (city).
    
    **Use Case:**
    - Find roommates in specific city
    - Browse profiles by location
    
    **Future Enhancement:**
    - Add radius-based search with PostGIS
    - Add coordinate-based proximity search
    
    Args:
        city: City name (partial match supported)
        limit: Maximum number of results (1-100)
    
    Returns:
        List of matching profiles
    """
    return await profile_service.search_profiles_by_location(
        db=db,
        city=city,
        limit=limit
    )


@router.get("/search/availability", response_model=list[UserProfileResponse])
async def search_profiles_by_availability(
    target_date: date = Query(..., description="Target move-in date"),
    short_term: Optional[bool] = Query(None, description="Filter by short-term preference"),
    long_term: Optional[bool] = Query(None, description="Filter by long-term preference"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search profiles by move-in availability.
    
    **Use Case:**
    - Find roommates available on specific date
    - Filter by lease term preference
    
    Args:
        target_date: Date to check availability (YYYY-MM-DD)
        short_term: Filter by short-term preference
        long_term: Filter by long-term preference
        limit: Maximum number of results
    
    Returns:
        List of profiles available around target date
    
    **Logic:**
    - Returns profiles where:
      - move_in_date_earliest <= target_date <= move_in_date_latest
      - Matches term preferences if specified
    """
    return await profile_service.get_profiles_by_availability(
        db=db,
        target_date=target_date,
        looking_for_short_term=short_term,
        looking_for_long_term=long_term,
        limit=limit
    )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get another user's profile (public view).
    
    **Use Case:**
    - View profile of potential match
    - Browse roommate profiles
    
    **Privacy:**
    - Returns public profile information
    - Does not expose sensitive fields
    
    Args:
        user_id: ID of user whose profile to retrieve
    
    Returns:
        User profile
    
    Raises:
        404: If profile not found
    """
    profile = await profile_service.get_profile(db, user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return profile


@router.get("/{user_id}/completeness")
async def get_user_profile_completeness(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get profile completeness for another user.
    
    **Use Case:**
    - Assess how complete a potential match's profile is
    - Filter for users with complete profiles
    
    Args:
        user_id: ID of user to check
    
    Returns:
        Completeness information dict
    """
    return await profile_service.get_profile_completeness(db, user_id)


# Export router to include in main app
__all__ = ["router"]