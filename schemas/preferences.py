"""
Pydantic schemas for user preferences.
Separated from user.py for better organization.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class CleanlinessLevel(str, Enum):
    """Cleanliness preference levels."""
    VERY_CLEAN = "very_clean"
    CLEAN = "clean"
    MODERATE = "moderate"
    RELAXED = "relaxed"


class SleepSchedule(str, Enum):
    """Sleep schedule types."""
    EARLY_BIRD = "early_bird"
    NORMAL = "normal"
    NIGHT_OWL = "night_owl"


class GuestFrequency(str, Enum):
    """Guest frequency levels."""
    NEVER = "never"
    RARELY = "rarely"
    SOMETIMES = "sometimes"
    OFTEN = "often"


class PreferencesBase(BaseModel):
    """Base preferences schema with common fields."""
    budget_min: int = Field(..., gt=0, description="Minimum budget in currency units")
    budget_max: int = Field(..., gt=0, description="Maximum budget in currency units")
    cleanliness_level: CleanlinessLevel
    sleep_schedule: SleepSchedule
    smoking_ok: bool = Field(default=False, description="Is smoking acceptable")
    drinking_ok: bool = Field(default=True, description="Is drinking acceptable")
    pets_ok: bool = Field(default=False, description="Are pets acceptable")
    guest_frequency: GuestFrequency
    is_student: bool = Field(default=False, description="Is user a student")
    is_working: bool = Field(default=False, description="Is user working")
    
    @field_validator('budget_max')
    @classmethod
    def validate_budget_range(cls, v, info):
        """Ensure budget_max >= budget_min."""
        if 'budget_min' in info.data and v < info.data['budget_min']:
            raise ValueError("budget_max must be greater than or equal to budget_min")
        return v


class PreferencesCreate(PreferencesBase):
    """Schema for creating preferences."""
    pass


class PreferencesUpdate(BaseModel):
    """Schema for updating preferences (all fields optional)."""
    budget_min: Optional[int] = Field(None, gt=0)
    budget_max: Optional[int] = Field(None, gt=0)
    cleanliness_level: Optional[CleanlinessLevel] = None
    sleep_schedule: Optional[SleepSchedule] = None
    smoking_ok: Optional[bool] = None
    drinking_ok: Optional[bool] = None
    pets_ok: Optional[bool] = None
    guest_frequency: Optional[GuestFrequency] = None
    is_student: Optional[bool] = None
    is_working: Optional[bool] = None
    
    @field_validator('budget_max')
    @classmethod
    def validate_budget_range(cls, v, info):
        """Ensure budget_max >= budget_min if both provided."""
        if v is not None and 'budget_min' in info.data:
            budget_min = info.data.get('budget_min')
            if budget_min is not None and v < budget_min:
                raise ValueError("budget_max must be greater than or equal to budget_min")
        return v


class PreferencesResponse(PreferencesBase):
    """Schema for preferences response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class PreferencesDetailResponse(BaseModel):
    """Detailed preferences response with additional info."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    budget_min: int
    budget_max: int
    budget_display: str  # Computed field like "$1000 - $1500"
    cleanliness_level: CleanlinessLevel
    cleanliness_display: str  # Human-readable
    sleep_schedule: SleepSchedule
    sleep_display: str  # Human-readable
    smoking_ok: bool
    drinking_ok: bool
    pets_ok: bool
    guest_frequency: GuestFrequency
    guest_display: str  # Human-readable
    is_student: bool
    is_working: bool
    work_status_display: str  # Computed
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_preferences(cls, prefs: PreferencesResponse) -> "PreferencesDetailResponse":
        """Create detailed response from basic preferences."""
        return cls(
            id=prefs.id,
            user_id=prefs.user_id,
            budget_min=prefs.budget_min,
            budget_max=prefs.budget_max,
            budget_display=f"${prefs.budget_min} - ${prefs.budget_max}",
            cleanliness_level=prefs.cleanliness_level,
            cleanliness_display=cls._cleanliness_display(prefs.cleanliness_level),
            sleep_schedule=prefs.sleep_schedule,
            sleep_display=cls._sleep_display(prefs.sleep_schedule),
            smoking_ok=prefs.smoking_ok,
            drinking_ok=prefs.drinking_ok,
            pets_ok=prefs.pets_ok,
            guest_frequency=prefs.guest_frequency,
            guest_display=cls._guest_display(prefs.guest_frequency),
            is_student=prefs.is_student,
            is_working=prefs.is_working,
            work_status_display=cls._work_status_display(prefs.is_student, prefs.is_working),
            created_at=prefs.created_at,
            updated_at=prefs.updated_at
        )
    
    @staticmethod
    def _cleanliness_display(level: CleanlinessLevel) -> str:
        """Convert cleanliness level to display string."""
        displays = {
            CleanlinessLevel.VERY_CLEAN: "Very Clean",
            CleanlinessLevel.CLEAN: "Clean",
            CleanlinessLevel.MODERATE: "Moderate",
            CleanlinessLevel.RELAXED: "Relaxed"
        }
        return displays.get(level, level.value)
    
    @staticmethod
    def _sleep_display(schedule: SleepSchedule) -> str:
        """Convert sleep schedule to display string."""
        displays = {
            SleepSchedule.EARLY_BIRD: "Early Bird (before 10pm)",
            SleepSchedule.NORMAL: "Normal (10pm-12am)",
            SleepSchedule.NIGHT_OWL: "Night Owl (after 12am)"
        }
        return displays.get(schedule, schedule.value)
    
    @staticmethod
    def _guest_display(frequency: GuestFrequency) -> str:
        """Convert guest frequency to display string."""
        displays = {
            GuestFrequency.NEVER: "Never",
            GuestFrequency.RARELY: "Rarely (few times per month)",
            GuestFrequency.SOMETIMES: "Sometimes (weekly)",
            GuestFrequency.OFTEN: "Often (multiple times per week)"
        }
        return displays.get(frequency, frequency.value)
    
    @staticmethod
    def _work_status_display(is_student: bool, is_working: bool) -> str:
        """Convert work status to display string."""
        if is_student and is_working:
            return "Student & Working"
        elif is_student:
            return "Student"
        elif is_working:
            return "Working Professional"
        else:
            return "Other"