"""
FastAPI routes for roommate matching.
Thin layer - business logic in MatchingService.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import get_db
from models.user import User
from schemas.user import MatchListResponse
from services.matching_service import MatchingService
from api.dependencies import get_current_active_user


router = APIRouter(prefix="/matches", tags=["Matching"])
matching_service = MatchingService()


@router.get("", response_model=MatchListResponse)
async def get_matches(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    min_score: int = Query(None, ge=0, le=100, description="Minimum compatibility score"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get ranked roommate matches for current user.
    
    **Algorithm:**
    - Deterministic, explainable matching
    - Score range: 0-100
    - Default minimum: 30 (configurable)
    
    **Score Components:**
    - Budget overlap: 20 points
    - Location proximity: 25 points
    - Cleanliness match: 15 points
    - Sleep schedule: 10 points
    - Lifestyle compatibility: 15 points
    - Availability: 10 points
    - Reputation bonus: 5 points
    
    **Each Match Includes:**
    - User profile
    - Compatibility score
    - Top 3 matching reasons with point values
    - List of potential conflicts
    - Distance in kilometers
    - Budget overlap range
    
    **Requirements:**
    - User must have complete profile
    - User must have set preferences
    - User account must be active
    
    **Filtering:**
    - Automatically excludes matches below min_score
    - Sorted by score (highest first)
    - Paginated results
    
    Args:
        page: Page number (starting from 1)
        page_size: Number of results per page (1-100)
        min_score: Minimum compatibility score filter (0-100)
    
    Returns:
        List of matches with explanations, total count, pagination info
    
    Raises:
        400: If profile or preferences missing
        403: If account not active
    
    **Example Response:**
    ```json
    {
      "matches": [
        {
          "user_id": 123,
          "score": 87,
          "profile": {...},
          "explanation": {
            "score": 87,
            "top_reasons": [
              {"reason": "location_close", "points": 25},
              {"reason": "budget_match", "points": 18},
              {"reason": "cleanliness_match", "points": 15}
            ],
            "conflicts": [],
            "distance_km": 3.2,
            "budget_overlap_min": 1200,
            "budget_overlap_max": 1500
          }
        }
      ],
      "total": 15,
      "page": 1,
      "page_size": 20
    }
    ```
    """
    # Verify user has complete profile
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete your profile first. Visit /api/v1/profiles to create one."
        )
    
    # Verify user has set preferences
    if not current_user.preferences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please set your preferences first. Visit /api/v1/preferences to create them."
        )
    
    # Get matches from service
    matches = await matching_service.find_matches(
        db=db,
        user_id=current_user.id,
        limit=page_size,
        min_score=min_score
    )
    
    return MatchListResponse(
        matches=matches,
        total=len(matches),
        page=page,
        page_size=page_size
    )


@router.get("/explain/{target_user_id}")
async def explain_match(
    target_user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed match explanation for a specific user.
    
    **Use Case:**
    - Deep dive into why two users match
    - Understand compatibility factors
    - Review potential conflicts before messaging
    
    **Returns detailed breakdown:**
    - Score by component
    - All reasons (not just top 3)
    - Detailed conflict analysis
    - Distance and location info
    - Budget compatibility details
    
    Args:
        target_user_id: ID of user to analyze match with
    
    Returns:
        Detailed match explanation
    
    Raises:
        400: If trying to match with self or missing profile/preferences
        404: If target user not found or incomplete
    """
    if current_user.id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot match with yourself"
        )
    
    # Verify user has complete profile
    if not current_user.profile or not current_user.preferences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete your profile and preferences first"
        )
    
    # Get single match explanation
    matches = await matching_service.find_matches(
        db=db,
        user_id=current_user.id,
        limit=100,  # Get larger set to find target
        min_score=0  # Include all scores
    )
    
    # Find target user in matches
    target_match = next((m for m in matches if m.user_id == target_user_id), None)
    
    if not target_match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found or has incomplete profile/preferences"
        )
    
    return target_match


# Export router
__all__ = ["router"]