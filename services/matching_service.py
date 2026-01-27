"""
Matching service - orchestration layer.
Bridges database models and pure matching engine.
"""
from typing import List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.matching.engine import (
    MatchingEngineV1,
    UserMatchProfile,
    MatchResult
)
from models.user import User, UserProfile, UserPreferences, Reputation
from schemas.user import MatchResponse, MatchExplanationResponse, MatchReasonResponse
from config import get_settings


settings = get_settings()


class MatchingService:
    """Service for matching operations."""
    
    def __init__(self):
        self.engine = MatchingEngineV1(
            max_distance_km=settings.matching_max_distance_km
        )
    
    async def find_matches(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 20,
        min_score: int = None
    ) -> List[MatchResponse]:
        """
        Find matches for a user.
        
        Args:
            db: Database session
            user_id: ID of user seeking matches
            limit: Maximum number of matches to return
            min_score: Minimum compatibility score (default from config)
        
        Returns:
            List of MatchResponse objects sorted by score
        """
        min_score = min_score or settings.matching_min_score_threshold
        
        # Load seeker's complete profile
        seeker_profile = await self._load_user_match_profile(db, user_id)
        if not seeker_profile:
            return []
        
        # Load candidate profiles
        # TODO: Add more sophisticated filtering (location radius, budget range)
        candidate_profiles = await self._load_candidate_profiles(
            db,
            user_id,
            seeker_profile
        )
        
        # Calculate matches
        match_results: List[MatchResult] = []
        for candidate in candidate_profiles:
            result = self.engine.calculate_match(seeker_profile, candidate)
            if result.score >= min_score:
                match_results.append(result)
        
        # Sort by score descending
        match_results.sort(key=lambda x: x.score, reverse=True)
        match_results = match_results[:limit]
        
        # Convert to response format with user profiles
        matches = await self._enrich_matches(db, match_results)
        
        return matches
    
    async def _load_user_match_profile(
        self,
        db: AsyncSession,
        user_id: int
    ) -> UserMatchProfile | None:
        """Load user's complete match profile."""
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.profile),
                selectinload(User.preferences),
                selectinload(User.reputation)
            )
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.profile or not user.preferences:
            return None
        
        # Ensure reputation exists
        reputation_score = user.reputation.score if user.reputation else 100
        
        return UserMatchProfile(
            user_id=user.id,
            age=user.profile.age,
            latitude=user.profile.latitude,
            longitude=user.profile.longitude,
            city=user.profile.city,
            looking_for_short_term=user.profile.looking_for_short_term,
            looking_for_long_term=user.profile.looking_for_long_term,
            move_in_earliest=(
                user.profile.move_in_date_earliest.isoformat()
                if user.profile.move_in_date_earliest else None
            ),
            move_in_latest=(
                user.profile.move_in_date_latest.isoformat()
                if user.profile.move_in_date_latest else None
            ),
            budget_min=user.preferences.budget_min,
            budget_max=user.preferences.budget_max,
            cleanliness_level=user.preferences.cleanliness_level.value,
            sleep_schedule=user.preferences.sleep_schedule.value,
            smoking_ok=user.preferences.smoking_ok,
            drinking_ok=user.preferences.drinking_ok,
            pets_ok=user.preferences.pets_ok,
            guest_frequency=user.preferences.guest_frequency.value,
            is_student=user.preferences.is_student,
            is_working=user.preferences.is_working,
            reputation_score=reputation_score
        )
    
    async def _load_candidate_profiles(
        self,
        db: AsyncSession,
        seeker_id: int,
        seeker_profile: UserMatchProfile
    ) -> List[UserMatchProfile]:
        """
        Load candidate profiles for matching.
        Applies basic filters to reduce candidate pool.
        """
        # TODO: Add spatial indexing and more sophisticated filtering
        # For now, exclude seeker and load all active users with complete profiles
        
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.profile),
                selectinload(User.preferences),
                selectinload(User.reputation)
            )
            .where(
                and_(
                    User.id != seeker_id,
                    User.account_state == "active",
                    User.profile.has(),
                    User.preferences.has()
                )
            )
            .limit(100)  # Limit candidates for performance
        )
        users = result.scalars().all()
        
        profiles = []
        for user in users:
            if user.profile and user.preferences:
                reputation_score = user.reputation.score if user.reputation else 100
                
                profile = UserMatchProfile(
                    user_id=user.id,
                    age=user.profile.age,
                    latitude=user.profile.latitude,
                    longitude=user.profile.longitude,
                    city=user.profile.city,
                    looking_for_short_term=user.profile.looking_for_short_term,
                    looking_for_long_term=user.profile.looking_for_long_term,
                    move_in_earliest=(
                        user.profile.move_in_date_earliest.isoformat()
                        if user.profile.move_in_date_earliest else None
                    ),
                    move_in_latest=(
                        user.profile.move_in_date_latest.isoformat()
                        if user.profile.move_in_date_latest else None
                    ),
                    budget_min=user.preferences.budget_min,
                    budget_max=user.preferences.budget_max,
                    cleanliness_level=user.preferences.cleanliness_level.value,
                    sleep_schedule=user.preferences.sleep_schedule.value,
                    smoking_ok=user.preferences.smoking_ok,
                    drinking_ok=user.preferences.drinking_ok,
                    pets_ok=user.preferences.pets_ok,
                    guest_frequency=user.preferences.guest_frequency.value,
                    is_student=user.preferences.is_student,
                    is_working=user.preferences.is_working,
                    reputation_score=reputation_score
                )
                profiles.append(profile)
        
        return profiles
    
    async def _enrich_matches(
        self,
        db: AsyncSession,
        match_results: List[MatchResult]
    ) -> List[MatchResponse]:
        """Enrich match results with full user profiles."""
        if not match_results:
            return []
        
        user_ids = [m.user_id for m in match_results]
        
        result = await db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id.in_(user_ids))
        )
        users = {user.id: user for user in result.scalars().all()}
        
        enriched_matches = []
        for match in match_results:
            user = users.get(match.user_id)
            if user and user.profile:
                explanation = MatchExplanationResponse(
                    score=match.explanation.score,
                    top_reasons=[
                        MatchReasonResponse(
                            reason=reason.value,
                            points=points
                        )
                        for reason, points in match.explanation.top_reasons
                    ],
                    conflicts=[c.value for c in match.explanation.conflicts],
                    distance_km=match.explanation.distance_km,
                    budget_overlap_min=match.explanation.budget_overlap[0],
                    budget_overlap_max=match.explanation.budget_overlap[1]
                )
                
                # Convert profile to response
                from schemas.user import UserProfileResponse
                profile_response = UserProfileResponse.model_validate(user.profile)
                
                match_response = MatchResponse(
                    user_id=match.user_id,
                    score=match.score,
                    profile=profile_response,
                    explanation=explanation
                )
                enriched_matches.append(match_response)
        
        return enriched_matches