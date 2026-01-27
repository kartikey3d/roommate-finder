"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# Enums (matching models)
class AccountState(str, Enum):
    UNVERIFIED = "unverified"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class CleanlinessLevel(str, Enum):
    VERY_CLEAN = "very_clean"
    CLEAN = "clean"
    MODERATE = "moderate"
    RELAXED = "relaxed"


class SleepSchedule(str, Enum):
    EARLY_BIRD = "early_bird"
    NORMAL = "normal"
    NIGHT_OWL = "night_owl"


class GuestFrequency(str, Enum):
    NEVER = "never"
    RARELY = "rarely"
    SOMETIMES = "sometimes"
    OFTEN = "often"


# Auth Schemas
class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=18, le=100)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# User Profile Schemas
class UserProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=18, le=100)
    gender: Optional[Gender] = None
    bio: Optional[str] = Field(None, max_length=500)
    city: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    looking_for_short_term: bool = False
    looking_for_long_term: bool = True
    move_in_date_earliest: Optional[date] = None
    move_in_date_latest: Optional[date] = None


class UserProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=18, le=100)
    gender: Optional[Gender] = None
    bio: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    looking_for_short_term: Optional[bool] = None
    looking_for_long_term: Optional[bool] = None
    move_in_date_earliest: Optional[date] = None
    move_in_date_latest: Optional[date] = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    name: str
    age: int
    gender: Optional[Gender]
    bio: Optional[str]
    city: str
    latitude: float
    longitude: float
    looking_for_short_term: bool
    looking_for_long_term: bool
    move_in_date_earliest: Optional[date]
    move_in_date_latest: Optional[date]
    created_at: datetime
    updated_at: datetime


# Preferences Schemas
class UserPreferencesCreate(BaseModel):
    budget_min: int = Field(..., gt=0)
    budget_max: int = Field(..., gt=0)
    cleanliness_level: CleanlinessLevel
    sleep_schedule: SleepSchedule
    smoking_ok: bool = False
    drinking_ok: bool = True
    pets_ok: bool = False
    guest_frequency: GuestFrequency
    is_student: bool = False
    is_working: bool = False
    
    @property
    def validate_budget(self):
        if self.budget_max < self.budget_min:
            raise ValueError("budget_max must be >= budget_min")
        return self


class UserPreferencesUpdate(BaseModel):
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


class UserPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    budget_min: int
    budget_max: int
    cleanliness_level: CleanlinessLevel
    sleep_schedule: SleepSchedule
    smoking_ok: bool
    drinking_ok: bool
    pets_ok: bool
    guest_frequency: GuestFrequency
    is_student: bool
    is_working: bool
    created_at: datetime
    updated_at: datetime


# Complete User Schema
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    account_state: AccountState
    created_at: datetime
    profile: Optional[UserProfileResponse] = None
    preferences: Optional[UserPreferencesResponse] = None


# Matching Schemas
class MatchReasonResponse(BaseModel):
    reason: str
    points: int


class MatchExplanationResponse(BaseModel):
    score: int
    top_reasons: List[MatchReasonResponse]
    conflicts: List[str]
    distance_km: float
    budget_overlap_min: int
    budget_overlap_max: int


class MatchResponse(BaseModel):
    user_id: int
    score: int
    profile: UserProfileResponse
    explanation: MatchExplanationResponse


class MatchListResponse(BaseModel):
    matches: List[MatchResponse]
    total: int
    page: int
    page_size: int


# Pagination
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)