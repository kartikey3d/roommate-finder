"""
Pydantic schemas for messaging system.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageStatus(str, Enum):
    """Message status types."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class MessageRequest(BaseModel):
    """Request to send a message."""
    recipient_id: int = Field(..., gt=0, description="ID of message recipient")
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Message content"
    )


class MessageResponse(BaseModel):
    """Response for a single message."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    sender_id: int
    recipient_id: int
    content: str
    status: MessageStatus
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    is_deleted_by_sender: bool
    is_deleted_by_recipient: bool


class MessageWithUserInfo(MessageResponse):
    """Message response with sender/recipient info."""
    sender_name: str
    recipient_name: str


class ConversationPreview(BaseModel):
    """Preview of a conversation for listing."""
    model_config = ConfigDict(from_attributes=True)
    
    conversation_id: int
    other_user_id: int
    other_user_name: str
    last_message_content: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int
    created_at: datetime


class ConversationDetail(BaseModel):
    """Detailed conversation with messages."""
    conversation_id: int
    other_user_id: int
    other_user_name: str
    messages: List[MessageResponse]
    total_messages: int
    unread_count: int


class MessageListResponse(BaseModel):
    """Paginated message list response."""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ConversationListResponse(BaseModel):
    """List of conversations."""
    conversations: List[ConversationPreview]
    total: int
    unread_total: int


class MessageStatusUpdate(BaseModel):
    """Update message status."""
    status: MessageStatus


class MarkAsReadRequest(BaseModel):
    """Request to mark messages as read."""
    message_ids: List[int] = Field(..., min_length=1, max_length=100)


class UnreadCountResponse(BaseModel):
    """Unread message count."""
    unread_count: int
    conversations_with_unread: int