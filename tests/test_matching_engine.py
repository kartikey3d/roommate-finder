"""
Unit tests for matching engine.
Tests pure domain logic without database dependencies.
"""
import pytest
from core.matching.engine import (
    MatchingEngineV1,
    UserMatchProfile,
    MatchReason,
    ConflictWarning
)


@pytest.fixture
def engine():
    """Create matching engine instance."""
    return MatchingEngineV1(max_distance_km=50.0)


@pytest.fixture
def base_profile():
    """Create a base user profile for testing."""
    return UserMatchProfile(
        user_id=1,
        age=25,
        latitude=37.7749,
        longitude=-122.4194,
        city="San Francisco",
        looking_for_short_term=False,
        looking_for_long_term=True,
        move_in_earliest=None,
        move_in_latest=None,
        budget_min=1000,
        budget_max=1500,
        cleanliness_level="clean",
        sleep_schedule="normal",
        smoking_ok=False,
        drinking_ok=True,
        pets_ok=False,
        guest_frequency="sometimes",
        is_student=False,
        is_working=True,
        reputation_score=100
    )


class TestBudgetCompatibility:
    """Test budget matching logic."""
    
    def test_perfect_budget_overlap(self, engine, base_profile):
        """Test identical budget ranges."""
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "budget_min": 1000,
            "budget_max": 1500
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Budget should be a top reason
        budget_reasons = [r for r in result.explanation.top_reasons 
                         if r[0] == MatchReason.BUDGET_MATCH]
        assert len(budget_reasons) > 0
        assert budget_reasons[0][1] == 20  # Full budget points
    
    def test_partial_budget_overlap(self, engine, base_profile):
        """Test partial budget overlap."""
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "budget_min": 1200,
            "budget_max": 1800
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Should have some budget points but not full
        assert result.score > 0
        assert result.explanation.budget_overlap == (1200, 1500)
    
    def test_no_budget_overlap(self, engine, base_profile):
        """Test no budget overlap."""
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "budget_min": 2000,
            "budget_max": 2500
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Should have budget mismatch conflict
        assert ConflictWarning.BUDGET_MISMATCH in result.explanation.conflicts
        assert result.explanation.budget_overlap == (0, 0)


class TestLocationCompatibility:
    """Test location-based matching."""
    
    def test_same_location(self, engine, base_profile):
        """Test users at same location."""
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Distance should be ~0
        assert result.explanation.distance_km < 0.1
        # Should get full location points
        location_reasons = [r for r in result.explanation.top_reasons 
                           if r[0] == MatchReason.LOCATION_CLOSE]
        assert len(location_reasons) > 0
    
    def test_far_location(self, engine, base_profile):
        """Test users far apart."""
        # New York coordinates (far from San Francisco)
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York"
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Distance should be ~4000 km
        assert result.explanation.distance_km > 1000
        # Should have location conflict
        assert ConflictWarning.LOCATION_FAR in result.explanation.conflicts


class TestCleanlinessCompatibility:
    """Test cleanliness matching."""
    
    def test_same_cleanliness(self, engine, base_profile):
        """Test identical cleanliness levels."""
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "cleanliness_level": "clean"
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Should get full cleanliness points
        cleanliness_reasons = [r for r in result.explanation.top_reasons 
                              if r[0] == MatchReason.CLEANLINESS_MATCH]
        assert len(cleanliness_reasons) > 0
        assert cleanliness_reasons[0][1] == 15
    
    def test_incompatible_cleanliness(self, engine, base_profile):
        """Test incompatible cleanliness levels."""
        # Very clean vs relaxed
        base_profile.cleanliness_level = "very_clean"
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "cleanliness_level": "relaxed"
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Should have cleanliness conflict
        assert ConflictWarning.CLEANLINESS_CONFLICT in result.explanation.conflicts


class TestSleepScheduleCompatibility:
    """Test sleep schedule matching."""
    
    def test_compatible_sleep_schedules(self, engine, base_profile):
        """Test compatible sleep schedules."""
        base_profile.sleep_schedule = "early_bird"
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "sleep_schedule": "normal"
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Should have decent sleep compatibility (0.7 * 10 = 7 points)
        sleep_reasons = [r for r in result.explanation.top_reasons 
                        if r[0] == MatchReason.SLEEP_SCHEDULE_MATCH]
        assert len(sleep_reasons) > 0
    
    def test_incompatible_sleep_schedules(self, engine, base_profile):
        """Test incompatible sleep schedules."""
        base_profile.sleep_schedule = "early_bird"
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "sleep_schedule": "night_owl"
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Should have sleep conflict
        assert ConflictWarning.SLEEP_CONFLICT in result.explanation.conflicts


class TestLifestyleCompatibility:
    """Test lifestyle factor matching."""
    
    def test_smoking_conflict(self, engine, base_profile):
        """Test smoking incompatibility."""
        base_profile.smoking_ok = False
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "smoking_ok": True
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Should have smoking conflict
        assert ConflictWarning.SMOKING_CONFLICT in result.explanation.conflicts
    
    def test_pets_conflict(self, engine, base_profile):
        """Test pets incompatibility."""
        base_profile.pets_ok = False
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "pets_ok": True
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Should have pets conflict
        assert ConflictWarning.PETS_CONFLICT in result.explanation.conflicts


class TestOverallMatching:
    """Test complete matching scenarios."""
    
    def test_perfect_match(self, engine, base_profile):
        """Test near-perfect match."""
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Should have very high score
        assert result.score >= 90
        # Should have multiple match reasons
        assert len(result.explanation.top_reasons) >= 3
        # Should have no conflicts
        assert len(result.explanation.conflicts) == 0
    
    def test_poor_match(self, engine, base_profile):
        """Test poor match with multiple conflicts."""
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "budget_min": 3000,
            "budget_max": 4000,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "cleanliness_level": "relaxed",
            "sleep_schedule": "night_owl",
            "smoking_ok": True,
            "pets_ok": True
        })
        base_profile.cleanliness_level = "very_clean"
        base_profile.sleep_schedule = "early_bird"
        base_profile.smoking_ok = False
        base_profile.pets_ok = False
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Should have low score
        assert result.score < 30
        # Should have multiple conflicts
        assert len(result.explanation.conflicts) >= 3
    
    def test_score_range(self, engine, base_profile):
        """Test that scores stay in valid range."""
        candidate = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2
        })
        
        result = engine.calculate_match(base_profile, candidate)
        
        # Score must be 0-100
        assert 0 <= result.score <= 100


class TestReputationBonus:
    """Test reputation score impact."""
    
    def test_high_reputation_bonus(self, engine, base_profile):
        """Test bonus for high reputation."""
        candidate_high_rep = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 2,
            "reputation_score": 100
        })
        
        candidate_low_rep = base_profile.__class__(**{
            **base_profile.__dict__,
            "user_id": 3,
            "reputation_score": 50
        })
        
        result_high = engine.calculate_match(base_profile, candidate_high_rep)
        result_low = engine.calculate_match(base_profile, candidate_low_rep)
        
        # High reputation should have higher score
        assert result_high.score > result_low.score


# Run tests with: pytest tests/test_matching_engine.py -v