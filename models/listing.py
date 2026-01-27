"""
SQLAlchemy models for room listings.
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
    from .user import User


class ListingStatus(str, PyEnum):
    """Listing status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FILLED = "filled"


class LeaseDuration(str, PyEnum):
    """Lease duration types."""
    SHORT_TERM = "short_term"  # < 6 months
    LONG_TERM = "long_term"  # >= 6 months
    FLEXIBLE = "flexible"


class RoomListing(Base):
    """Room listing created by users."""
    __tablename__ = "room_listings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic info
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Financial
    rent: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    deposit: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Location
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Availability
    available_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    lease_duration: Mapped[LeaseDuration] = mapped_column(Enum(LeaseDuration), nullable=False)
    
    # Amenities (stored as JSONB for flexibility)
    amenities: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Example: {"wifi": true, "parking": true, "furnished": false, "laundry": "in_unit"}
    
    # Status
    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus),
        default=ListingStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="listings")
    
    __table_args__ = (
        Index("idx_listing_location", "latitude", "longitude"),
        Index("idx_listing_rent", "rent"),
        Index("idx_listing_available", "available_from"),
        CheckConstraint("rent > 0", name="rent_positive"),
        CheckConstraint("deposit >= 0", name="deposit_non_negative"),
    )