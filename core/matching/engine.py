"""
Core matching engine - pure Python, framework-agnostic.
Implements deterministic, explainable roommate matching.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum
import math


class MatchReason(str, Enum):
    """Reasons for match compatibility."""
    BUDGET_MATCH = "budget_match"
    LOCATION_CLOSE = "location_close"
    CLEANLINESS_MATCH = "cleanliness_match"
    SLEEP_SCHEDULE_MATCH = "sleep_schedule_match"
    LIFESTYLE_MATCH = "lifestyle_match"
    AVAILABILITY_MATCH = "availability_match"
    WORK_STATUS_MATCH = "work_status_match"


class ConflictWarning(str, Enum):
    """Warnings for potential conflicts."""
    BUDGET_MISMATCH = "budget_mismatch"
    LOCATION_FAR = "location_far"
    CLEANLINESS_CONFLICT = "cleanliness_conflict"
    SLEEP_CONFLICT = "sleep_conflict"
    SMOKING_CONFLICT = "smoking_conflict"
    PETS_CONFLICT = "pets_conflict"
    GUEST_FREQUENCY_CONFLICT = "guest_frequency_conflict"


@dataclass
class UserMatchProfile:
    """
    User profile data needed for matching.
    Pure data structure, no ORM dependencies.
    """
    user_id: int
    
    # Profile
    age: int
    latitude: float
    longitude: float
    city: str
    looking_for_short_term: bool
    looking_for_long_term: bool
    move_in_earliest: Optional[str]  # ISO date string
    move_in_latest: Optional[str]
    
    # Preferences
    budget_min: int
    budget_max: int
    cleanliness_level: str
    sleep_schedule: str
    smoking_ok: bool
    drinking_ok: bool
    pets_ok: bool
    guest_frequency: str
    is_student: bool
    is_working: bool
    
    # Reputation
    reputation_score: int


@dataclass
class MatchExplanation:
    """Explanation for a match score."""
    score: int
    top_reasons: List[Tuple[MatchReason, int]]  # (reason, points)
    conflicts: List[ConflictWarning]
    distance_km: float
    budget_overlap: Tuple[int, int]  # (min, max)


@dataclass
class MatchResult:
    """Result of matching two users."""
    user_id: int
    score: int
    explanation: MatchExplanation


class MatchingEngineV1:
    """
    Deterministic matching engine using weighted heuristics.
    
    Score range: 0-100
    Threshold for relevance: 30+
    
    Weights:
    - Budget overlap: 20 points
    - Location proximity: 25 points
    - Cleanliness match: 15 points
    - Sleep schedule match: 10 points
    - Lifestyle compatibility: 15 points
    - Availability overlap: 10 points
    - Reputation bonus: 5 points
    """
    
    # Weight constants
    WEIGHT_BUDGET = 20
    WEIGHT_LOCATION = 25
    WEIGHT_CLEANLINESS = 15
    WEIGHT_SLEEP = 10
    WEIGHT_LIFESTYLE = 15
    WEIGHT_AVAILABILITY = 10
    WEIGHT_REPUTATION = 5
    
    # Distance thresholds (km)
    DISTANCE_EXCELLENT = 5
    DISTANCE_GOOD = 15
    DISTANCE_ACCEPTABLE = 30
    DISTANCE_FAR = 50
    
    # Cleanliness compatibility matrix
    CLEANLINESS_COMPATIBILITY = {
        ("very_clean", "very_clean"): 1.0,
        ("very_clean", "clean"): 0.8,
        ("very_clean", "moderate"): 0.4,
        ("very_clean", "relaxed"): 0.0,
        ("clean", "clean"): 1.0,
        ("clean", "moderate"): 0.7,
        ("clean", "relaxed"): 0.3,
        ("moderate", "moderate"): 1.0,
        ("moderate", "relaxed"): 0.7,
        ("relaxed", "relaxed"): 1.0,
    }
    
    # Sleep schedule compatibility
    SLEEP_COMPATIBILITY = {
        ("early_bird", "early_bird"): 1.0,
        ("early_bird", "normal"): 0.7,
        ("early_bird", "night_owl"): 0.2,
        ("normal", "normal"): 1.0,
        ("normal", "night_owl"): 0.7,
        ("night_owl", "night_owl"): 1.0,
    }
    
    def __init__(self, max_distance_km: float = 50.0):
        self.max_distance_km = max_distance_km
    
    def calculate_match(
        self,
        seeker: UserMatchProfile,
        candidate: UserMatchProfile
    ) -> MatchResult:
        """
        Calculate match score between seeker and candidate.
        
        Returns:
            MatchResult with score and explanation
        """
        score = 0
        reasons: List[Tuple[MatchReason, int]] = []
        conflicts: List[ConflictWarning] = []
        
        # 1. Budget compatibility (20 points)
        budget_score, budget_overlap = self._score_budget(seeker, candidate)
        score += budget_score
        if budget_score >= 15:
            reasons.append((MatchReason.BUDGET_MATCH, budget_score))
        elif budget_score < 10:
            conflicts.append(ConflictWarning.BUDGET_MISMATCH)
        
        # 2. Location proximity (25 points)
        distance_km = self._calculate_distance(
            seeker.latitude, seeker.longitude,
            candidate.latitude, candidate.longitude
        )
        location_score = self._score_location(distance_km)
        score += location_score
        if location_score >= 20:
            reasons.append((MatchReason.LOCATION_CLOSE, location_score))
        elif distance_km > self.DISTANCE_ACCEPTABLE:
            conflicts.append(ConflictWarning.LOCATION_FAR)
        
        # 3. Cleanliness compatibility (15 points)
        cleanliness_score = self._score_cleanliness(seeker, candidate)
        score += cleanliness_score
        if cleanliness_score >= 12:
            reasons.append((MatchReason.CLEANLINESS_MATCH, cleanliness_score))
        elif cleanliness_score < 6:
            conflicts.append(ConflictWarning.CLEANLINESS_CONFLICT)
        
        # 4. Sleep schedule (10 points)
        sleep_score = self._score_sleep_schedule(seeker, candidate)
        score += sleep_score
        if sleep_score >= 8:
            reasons.append((MatchReason.SLEEP_SCHEDULE_MATCH, sleep_score))
        elif sleep_score < 4:
            conflicts.append(ConflictWarning.SLEEP_CONFLICT)
        
        # 5. Lifestyle compatibility (15 points)
        lifestyle_score, lifestyle_conflicts = self._score_lifestyle(seeker, candidate)
        score += lifestyle_score
        if lifestyle_score >= 12:
            reasons.append((MatchReason.LIFESTYLE_MATCH, lifestyle_score))
        conflicts.extend(lifestyle_conflicts)
        
        # 6. Availability overlap (10 points)
        availability_score = self._score_availability(seeker, candidate)
        score += availability_score
        if availability_score >= 8:
            reasons.append((MatchReason.AVAILABILITY_MATCH, availability_score))
        
        # 7. Reputation bonus (5 points)
        reputation_score = self._score_reputation(candidate)
        score += reputation_score
        
        # Sort reasons by points (descending)
        reasons.sort(key=lambda x: x[1], reverse=True)
        
        explanation = MatchExplanation(
            score=int(score),
            top_reasons=reasons[:3],  # Top 3 reasons
            conflicts=conflicts,
            distance_km=round(distance_km, 2),
            budget_overlap=budget_overlap
        )
        
        return MatchResult(
            user_id=candidate.user_id,
            score=int(score),
            explanation=explanation
        )
    
    def _score_budget(
        self,
        seeker: UserMatchProfile,
        candidate: UserMatchProfile
    ) -> Tuple[int, Tuple[int, int]]:
        """Score budget compatibility."""
        overlap_min = max(seeker.budget_min, candidate.budget_min)
        overlap_max = min(seeker.budget_max, candidate.budget_max)
        
        if overlap_max < overlap_min:
            # No overlap
            return 0, (0, 0)
        
        overlap_range = overlap_max - overlap_min
        seeker_range = seeker.budget_max - seeker.budget_min
        candidate_range = candidate.budget_max - candidate.budget_min
        avg_range = (seeker_range + candidate_range) / 2
        
        if avg_range == 0:
            overlap_ratio = 1.0
        else:
            overlap_ratio = min(overlap_range / avg_range, 1.0)
        
        score = int(overlap_ratio * self.WEIGHT_BUDGET)
        return score, (overlap_min, overlap_max)
    
    def _calculate_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two coordinates using Haversine formula."""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _score_location(self, distance_km: float) -> int:
        """Score based on distance."""
        if distance_km <= self.DISTANCE_EXCELLENT:
            return self.WEIGHT_LOCATION
        elif distance_km <= self.DISTANCE_GOOD:
            ratio = 1 - ((distance_km - self.DISTANCE_EXCELLENT) /
                        (self.DISTANCE_GOOD - self.DISTANCE_EXCELLENT)) * 0.2
            return int(self.WEIGHT_LOCATION * ratio)
        elif distance_km <= self.DISTANCE_ACCEPTABLE:
            ratio = 1 - ((distance_km - self.DISTANCE_GOOD) /
                        (self.DISTANCE_ACCEPTABLE - self.DISTANCE_GOOD)) * 0.4
            return int(self.WEIGHT_LOCATION * ratio * 0.8)
        elif distance_km <= self.DISTANCE_FAR:
            ratio = 1 - ((distance_km - self.DISTANCE_ACCEPTABLE) /
                        (self.DISTANCE_FAR - self.DISTANCE_ACCEPTABLE))
            return int(self.WEIGHT_LOCATION * ratio * 0.4)
        else:
            return 0
    
    def _score_cleanliness(
        self,
        seeker: UserMatchProfile,
        candidate: UserMatchProfile
    ) -> int:
        """Score cleanliness compatibility."""
        pair = (seeker.cleanliness_level, candidate.cleanliness_level)
        reverse_pair = (candidate.cleanliness_level, seeker.cleanliness_level)
        
        compatibility = self.CLEANLINESS_COMPATIBILITY.get(
            pair,
            self.CLEANLINESS_COMPATIBILITY.get(reverse_pair, 0.5)
        )
        
        return int(compatibility * self.WEIGHT_CLEANLINESS)
    
    def _score_sleep_schedule(
        self,
        seeker: UserMatchProfile,
        candidate: UserMatchProfile
    ) -> int:
        """Score sleep schedule compatibility."""
        pair = (seeker.sleep_schedule, candidate.sleep_schedule)
        reverse_pair = (candidate.sleep_schedule, seeker.sleep_schedule)
        
        compatibility = self.SLEEP_COMPATIBILITY.get(
            pair,
            self.SLEEP_COMPATIBILITY.get(reverse_pair, 0.5)
        )
        
        return int(compatibility * self.WEIGHT_SLEEP)
    
    def _score_lifestyle(
        self,
        seeker: UserMatchProfile,
        candidate: UserMatchProfile
    ) -> Tuple[int, List[ConflictWarning]]:
        """Score lifestyle compatibility."""
        score = 0
        conflicts = []
        
        # Smoking (5 points)
        if seeker.smoking_ok == candidate.smoking_ok:
            score += 5
        elif not seeker.smoking_ok and candidate.smoking_ok:
            conflicts.append(ConflictWarning.SMOKING_CONFLICT)
        
        # Pets (5 points)
        if seeker.pets_ok == candidate.pets_ok:
            score += 5
        elif not seeker.pets_ok and candidate.pets_ok:
            conflicts.append(ConflictWarning.PETS_CONFLICT)
        
        # Guest frequency (5 points)
        guest_diff = abs(
            self._guest_frequency_value(seeker.guest_frequency) -
            self._guest_frequency_value(candidate.guest_frequency)
        )
        if guest_diff == 0:
            score += 5
        elif guest_diff == 1:
            score += 3
        elif guest_diff >= 3:
            conflicts.append(ConflictWarning.GUEST_FREQUENCY_CONFLICT)
        
        return score, conflicts
    
    def _guest_frequency_value(self, frequency: str) -> int:
        """Convert guest frequency to numeric value."""
        mapping = {
            "never": 0,
            "rarely": 1,
            "sometimes": 2,
            "often": 3
        }
        return mapping.get(frequency, 1)
    
    def _score_availability(
        self,
        seeker: UserMatchProfile,
        candidate: UserMatchProfile
    ) -> int:
        """Score availability compatibility."""
        # Check term compatibility
        seeker_terms = set()
        if seeker.looking_for_short_term:
            seeker_terms.add("short")
        if seeker.looking_for_long_term:
            seeker_terms.add("long")
        
        candidate_terms = set()
        if candidate.looking_for_short_term:
            candidate_terms.add("short")
        if candidate.looking_for_long_term:
            candidate_terms.add("long")
        
        if not seeker_terms.intersection(candidate_terms):
            return 0
        
        # TODO: Check date overlap when dates are present
        # For now, award full points if terms match
        return self.WEIGHT_AVAILABILITY
    
    def _score_reputation(self, candidate: UserMatchProfile) -> int:
        """Bonus points for good reputation."""
        # Linear scale: 0-100 reputation -> 0-5 points
        return int((candidate.reputation_score / 100) * self.WEIGHT_REPUTATION)