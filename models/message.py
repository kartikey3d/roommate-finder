"""
SQLAlchemy models for messaging system.
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String, Integer, Boolean, DateTime, Text,
    ForeignKey, Index, CheckConstraint, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .user import User


class MessageStatus(str, PyEnum):
    """Message status types."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class Message(Base):
    """Message between two users."""
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Participants
    sender_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    recipient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Status
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus),
        default=MessageStatus.SENT,
        nullable=False
    )
    
    # Timestamps
    sent_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Soft delete
    is_deleted_by_sender: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted_by_recipient: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    sender: Mapped["User"] = relationship(
        "User",
        foreign_keys=[sender_id],
        backref="sent_messages"
    )
    recipient: Mapped["User"] = relationship(
        "User",
        foreign_keys=[recipient_id],
        backref="received_messages"
    )
    
    __table_args__ = (
        Index("idx_conversation", "sender_id", "recipient_id"),
        Index("idx_recipient_unread", "recipient_id", "status"),
        CheckConstraint("sender_id != recipient_id", name="no_self_messaging"),
    )


class Conversation(Base):
    """
    Conversation metadata between two users.
    Tracks last message, unread count, etc.
    """
    __tablename__ = "conversations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Participants (always ordered: user1_id < user2_id)
    user1_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    user2_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Metadata
    last_message_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True
    )
    
    # Unread counts (per user)
    unread_count_user1: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unread_count_user2: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user1: Mapped["User"] = relationship("User", foreign_keys=[user1_id])
    user2: Mapped["User"] = relationship("User", foreign_keys=[user2_id])
    last_message: Mapped[Optional["Message"]] = relationship(
        "Message",
        foreign_keys=[last_message_id]
    )
    
    __table_args__ = (
        Index("idx_conversation_users", "user1_id", "user2_id", unique=True),
        CheckConstraint("user1_id < user2_id", name="ordered_user_ids"),
    )