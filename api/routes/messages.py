"""
FastAPI routes for messaging system.
Thin layer - business logic in MessagesService.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from models.base import get_db
from models.user import User
from schemas.messages import (
    MessageRequest,
    MessageResponse,
    MessageListResponse,
    ConversationListResponse,
    MarkAsReadRequest,
    UnreadCountResponse
)
from services.messages_service import MessagesService
from api.dependencies import get_current_active_user


router = APIRouter(prefix="/messages", tags=["Messages"])
messages_service = MessagesService()


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to another user.
    
    **Requirements:**
    - User must be active
    - Recipient must exist and be active
    - Cannot send to yourself
    - Message content 1-2000 characters
    
    **Rate Limiting:**
    - Maximum 50 messages per hour (TODO: implement)
    
    **Triggers:**
    - Emits `message_sent` event
    - Updates conversation metadata
    - Increments unread count for recipient
    - Can trigger reputation signals (spam detection)
    
    Args:
        message_data: Message content and recipient ID
    
    Returns:
        Created message with metadata
    
    Raises:
        400: If trying to message yourself or invalid recipient
        404: If recipient not found
        429: If rate limit exceeded (TODO)
    
    **Example:**
    ```json
    {
      "recipient_id": 123,
      "content": "Hi! I saw your profile and think we'd be great roommates!"
    }
    ```
    """
    return await messages_service.send_message(
        db=db,
        sender_id=current_user.id,
        message_data=message_data
    )


@router.get("", response_model=MessageListResponse)
async def get_messages(
    other_user_id: Optional[int] = Query(None, description="Filter by conversation with specific user"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Messages per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages for current user.
    
    **Without other_user_id:**
    - Returns all messages across all conversations
    - Sorted by most recent first
    - Paginated
    
    **With other_user_id:**
    - Returns only messages in that specific conversation
    - Includes both sent and received messages
    - Chronologically ordered
    
    **Deleted Messages:**
    - Soft deleted messages are excluded
    - Each user can delete independently
    
    Args:
        other_user_id: Optional - filter for specific conversation
        page: Page number (starting from 1)
        page_size: Results per page (1-100)
    
    Returns:
        Paginated list of messages with metadata
    
    **Example Response:**
    ```json
    {
      "messages": [
        {
          "id": 456,
          "sender_id": 123,
          "recipient_id": 789,
          "content": "Hello!",
          "status": "read",
          "sent_at": "2026-01-27T10:00:00Z",
          "read_at": "2026-01-27T10:05:00Z"
        }
      ],
      "total": 42,
      "page": 1,
      "page_size": 50,
      "has_more": false
    }
    ```
    """
    return await messages_service.get_user_messages(
        db=db,
        user_id=current_user.id,
        other_user_id=other_user_id,
        page=page,
        page_size=page_size
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all conversations for current user.
    
    **Returns:**
    - List of all conversations
    - Preview of last message (truncated to 100 chars)
    - Unread count per conversation
    - Total unread across all conversations
    
    **Sorted by:**
    - Most recent message first
    
    **Use Case:**
    - Display inbox/conversation list
    - Show unread indicators
    - Quick navigation to active conversations
    
    Returns:
        List of conversation previews with metadata
    
    **Example Response:**
    ```json
    {
      "conversations": [
        {
          "conversation_id": 1,
          "other_user_id": 123,
          "other_user_name": "John Doe",
          "last_message_content": "Thanks! When can we...",
          "last_message_at": "2026-01-27T15:30:00Z",
          "unread_count": 3,
          "created_at": "2026-01-25T10:00:00Z"
        }
      ],
      "total": 5,
      "unread_total": 8
    }
    ```
    """
    return await messages_service.get_conversations(
        db=db,
        user_id=current_user.id
    )


@router.get("/conversations/{other_user_id}", response_model=MessageListResponse)
async def get_conversation_messages(
    other_user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages in a specific conversation.
    
    **Alias for:** `GET /messages?other_user_id={id}`
    
    More RESTful endpoint for conversation-specific messages.
    
    Args:
        other_user_id: ID of other user in conversation
        page: Page number
        page_size: Messages per page
    
    Returns:
        Paginated messages in conversation
    """
    return await messages_service.get_conversation_messages(
        db=db,
        user_id=current_user.id,
        other_user_id=other_user_id,
        page=page,
        page_size=page_size
    )


@router.post("/mark-read")
async def mark_messages_as_read(
    request: MarkAsReadRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark specific messages as read.
    
    **Requirements:**
    - User must be the recipient
    - Messages must not already be read
    
    **Effects:**
    - Updates message status to 'read'
    - Sets read_at timestamp
    - Decrements unread count in conversation
    
    **Bulk Operation:**
    - Can mark up to 100 messages at once
    
    Args:
        request: List of message IDs to mark as read
    
    Returns:
        Number of messages marked as read
    
    **Example:**
    ```json
    {
      "message_ids": [123, 124, 125]
    }
    ```
    
    Response:
    ```json
    {
      "marked_count": 3
    }
    ```
    """
    count = await messages_service.mark_as_read(
        db=db,
        user_id=current_user.id,
        message_ids=request.message_ids
    )
    return {"marked_count": count}


@router.post("/conversations/{other_user_id}/mark-read")
async def mark_conversation_as_read(
    other_user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all messages in a conversation as read.
    
    **Use Case:**
    - User opens/views a conversation
    - Mark entire conversation as read with one call
    
    **Effects:**
    - Marks all unread messages from other_user as read
    - Resets unread count to zero
    
    Args:
        other_user_id: ID of other user in conversation
    
    Returns:
        Number of messages marked as read
    
    Response:
    ```json
    {
      "marked_count": 5
    }
    ```
    """
    count = await messages_service.mark_conversation_as_read(
        db=db,
        user_id=current_user.id,
        other_user_id=other_user_id
    )
    return {"marked_count": count}


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a message (soft delete).
    
    **Soft Delete:**
    - Message remains in database
    - Only hidden for deleting user
    - Other user can still see it
    - Both users can delete independently
    
    **Requirements:**
    - User must be sender or recipient
    
    Args:
        message_id: ID of message to delete
    
    Returns:
        204 No Content on success
    
    Raises:
        403: If user is not part of the conversation
        404: If message not found
    """
    deleted = await messages_service.delete_message(
        db=db,
        user_id=current_user.id,
        message_id=message_id
    )
    
    if not deleted:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )


@router.get("/unread/count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get total unread message count.
    
    **Returns:**
    - Total unread messages across all conversations
    - Number of conversations with unread messages
    
    **Use Case:**
    - Display badge count in navigation
    - Show notification indicator
    - Dashboard summary
    
    Returns:
        Unread count information
    
    **Example Response:**
    ```json
    {
      "unread_count": 12,
      "conversations_with_unread": 3
    }
    ```
    """
    return await messages_service.get_unread_count(
        db=db,
        user_id=current_user.id
    )


# Export router
__all__ = ["router"]