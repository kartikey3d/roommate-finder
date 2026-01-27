"""
FastAPI routes for user preferences management.
Thin layer - business logic in PreferencesService.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import get_db
from models.user import User
from schemas.preferences import (
    PreferencesCreate,
    PreferencesUpdate,
    PreferencesResponse,
    PreferencesDetailResponse
)
from services.preferences_service import PreferencesService
from api.dependencies import get_current_user, get_current_active_user


router = APIRouter(prefix="/preferences", tags=["Preferences"])
preferences_service = PreferencesService()


@router.post("", response_model=PreferencesResponse, status_code=status.HTTP_201_CREATED)
async def create_preferences(
    preferences_data: PreferencesCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create preferences for the current user.
    
    **Requirements:**
    - User must be authenticated and active
    - User must not already have preferences
    
    **Budget Validation:**
    - budget_max must be >= budget_min
    - Both must be > 0
    
    **Triggers:**
    - Emits `preferences_updated` event
    - Triggers async match computation
    
    Returns:
        Created preferences object
    """
    return await preferences_service.create_preferences(
        db=db,
        user_id=current_user.id,
        preferences_data=preferences_data
    )


@router.get("/me", response_model=PreferencesResponse)
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's preferences.
    
    Returns:
        User preferences
    
    Raises:
        404: If preferences not found
    """
    preferences = await preferences_service.get_preferences(db, current_user.id)
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found. Please create preferences first."
        )
    
    return preferences


@router.get("/me/detailed", response_model=PreferencesDetailResponse)
async def get_my_preferences_detailed(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's preferences with human-readable display values.
    
    Includes formatted strings for:
    - Budget range
    - Cleanliness level
    - Sleep schedule
    - Guest frequency
    - Work status
    
    Returns:
        Detailed preferences with display values
    
    Raises:
        404: If preferences not found
    """
    preferences = await preferences_service.get_preferences_or_404(db, current_user.id)
    return PreferencesDetailResponse.from_preferences(preferences)


@router.get("/me/summary")
async def get_my_preferences_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a quick summary of current user's preferences.
    
    Useful for dashboard/overview displays.
    
    Returns:
        Summary dict with key preferences in readable format
    """
    return await preferences_service.get_preference_summary(db, current_user.id)


@router.put("/me", response_model=PreferencesResponse)
async def update_my_preferences(
    update_data: PreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's preferences.
    
    **Partial Updates:**
    - All fields are optional
    - Only provided fields will be updated
    - Omitted fields remain unchanged
    
    **Budget Validation:**
    - If both budget_min and budget_max provided, max must be >= min
    - If only one provided, validated against existing value
    
    **Triggers:**
    - Emits `preferences_updated` event with changed fields
    - Triggers async match recomputation
    
    Returns:
        Updated preferences object
    
    Raises:
        404: If preferences not found
        400: If validation fails
    """
    return await preferences_service.update_preferences(
        db=db,
        user_id=current_user.id,
        update_data=update_data
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete current user's preferences.
    
    **Warning:**
    - This action cannot be undone
    - User will not appear in matches until preferences are recreated
    - All cached matches will be invalidated
    
    Returns:
        204 No Content on success
    
    Raises:
        404: If preferences not found
    """
    deleted = await preferences_service.delete_preferences(db, current_user.id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found"
        )


@router.get("/compatibility/{target_user_id}")
async def check_budget_compatibility(
    target_user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check budget compatibility with another user.
    
    **Use Case:**
    - Before initiating contact
    - Quick compatibility check
    - Filter potential matches
    
    Args:
        target_user_id: ID of user to check compatibility with
    
    Returns:
        Compatibility information including:
        - compatible: bool
        - overlap_range: (min, max) if compatible
        - overlap_percentage: float
        - reason: str if not compatible
    
    **Privacy Note:**
    - Only returns overlap information, not exact budgets
    - Respects user privacy while enabling matching
    """
    if current_user.id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot check compatibility with yourself"
        )
    
    return await preferences_service.validate_budget_compatibility(
        db=db,
        user_id=current_user.id,
        target_user_id=target_user_id
    )


@router.get("/{user_id}", response_model=PreferencesResponse)
async def get_user_preferences(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get another user's preferences (public view).
    
    **Use Case:**
    - View preferences of potential matches
    - Understand compatibility factors
    
    **Privacy:**
    - Only returns public preference information
    - Does not expose sensitive data
    
    Args:
        user_id: ID of user whose preferences to retrieve
    
    Returns:
        User preferences
    
    Raises:
        404: If preferences not found
    """
    preferences = await preferences_service.get_preferences(db, user_id)
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User preferences not found"
        )
    
    return preferences


# Export router to include in main app
__all__ = ["router"]