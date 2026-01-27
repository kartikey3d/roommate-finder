"""
SQLAlchemy models for users, profiles, and preferences.
Async-compatible with proper relationships.
"""
from datetime import datetime, date
from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Date, Text,
    ForeignKey, Index, CheckConstraint, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base

if TYPE_CHECKING:
    from .listing import RoomListing


class AccountState(str, PyEnum):
    """User account state."""
    UNVERIFIED = "unverified"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class Gender(str, PyEnum):
    """Gender options."""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class CleanlinessLevel(str, PyEnum):
    """Cleanliness preference levels."""
    VERY_CLEAN = "very_clean"
    CLEAN = "clean"
    MODERATE = "moderate"
    RELAXED = "relaxed"


class SleepSchedule(str, PyEnum):
    """Sleep schedule types."""
    EARLY_BIRD = "early_bird"  # Sleep before 10pm
    NORMAL = "normal"  # Sleep 10pm-12am
    NIGHT_OWL = "night_owl"  # Sleep after 12am


class GuestFrequency(str, PyEnum):
    """How often guests are hosted."""
    NEVER = "never"
    RARELY = "rarely"  # Few times per month
    SOMETIMES = "sometimes"  # Weekly
    OFTEN = "often"  # Multiple times per week


class User(Base):
    """Core user account."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    account_state: Mapped[AccountState] = mapped_column(
        Enum(AccountState),
        default=AccountState.UNVERIFIED,
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    preferences: Mapped[Optional["UserPreferences"]] = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    listings: Mapped[list["RoomListing"]] = relationship(
        "RoomListing",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    reputation: Mapped[Optional["Reputation"]] = relationship(
        "Reputation",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )


class UserProfile(Base):
    """User profile information."""
    __tablename__ = "user_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[Optional[Gender]] = mapped_column(Enum(Gender), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Location
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Availability
    looking_for_short_term: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    looking_for_long_term: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    move_in_date_earliest: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    move_in_date_latest: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Derived signals (computed from behavior, stored as JSONB)
    signals: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")
    
    __table_args__ = (
        Index("idx_location", "latitude", "longitude"),
        Index("idx_move_in_dates", "move_in_date_earliest", "move_in_date_latest"),
        CheckConstraint("age >= 18 AND age <= 100", name="valid_age"),
    )


class UserPreferences(Base):
    """User roommate preferences."""
    __tablename__ = "user_preferences"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    # Budget
    budget_min: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    budget_max: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Lifestyle
    cleanliness_level: Mapped[CleanlinessLevel] = mapped_column(
        Enum(CleanlinessLevel),
        nullable=False
    )
    sleep_schedule: Mapped[SleepSchedule] = mapped_column(Enum(SleepSchedule), nullable=False)
    smoking_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    drinking_ok: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pets_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    guest_frequency: Mapped[GuestFrequency] = mapped_column(
        Enum(GuestFrequency),
        nullable=False
    )
    
    # Status
    is_student: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_working: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preferences")
    
    __table_args__ = (
        CheckConstraint("budget_min > 0", name="budget_min_positive"),
        CheckConstraint("budget_max >= budget_min", name="budget_max_gte_min"),
        Index("idx_budget_range", "budget_min", "budget_max"),
    )


class Reputation(Base):
    """User reputation score."""
    __tablename__ = "reputation"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    score: Mapped[int] = mapped_column(Integer, default=100, nullable=False, index=True)
    
    # Counters
    ghosting_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spam_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    excessive_unmatch_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reputation")
    
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="score_range"),
    )