"""
Messages service - manages messaging operations.
Handles message sending, retrieval, and conversation management.
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from models.user import User
from models.message import Message, Conversation, MessageStatus
from schemas.messages import (
    MessageRequest,
    MessageResponse,
    ConversationPreview,
    ConversationListResponse,
    MessageListResponse,
    UnreadCountResponse
)
from events.definitions import publish_message_sent
from config import get_settings


settings = get_settings()


class MessagesService:
    """Service for messaging operations."""
    
    async def send_message(
        self,
        db: AsyncSession,
        sender_id: int,
        message_data: MessageRequest
    ) -> MessageResponse:
        """
        Send a message to another user.
        
        Args:
            db: Database session
            sender_id: ID of sender
            message_data: Message content and recipient
        
        Returns:
            Created message
        
        Raises:
            HTTPException: If recipient not found or validation fails
        """
        recipient_id = message_data.recipient_id
        
        # Validate recipient exists
        if sender_id == recipient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send message to yourself"
            )
        
        # Check recipient exists
        result = await db.execute(
            select(User).where(User.id == recipient_id)
        )
        recipient = result.scalar_one_or_none()
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient not found"
            )
        
        # Check if recipient account is active
        if recipient.account_state != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send message to inactive user"
            )
        
        # TODO: Check rate limiting
        # await self._check_rate_limit(db, sender_id)
        
        # Create message
        message = Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=message_data.content,
            status=MessageStatus.SENT,
            sent_at=datetime.utcnow()
        )
        
        db.add(message)
        await db.flush()
        await db.refresh(message)
        
        # Update or create conversation
        await self._update_conversation(
            db,
            sender_id,
            recipient_id,
            message.id,
            message.sent_at
        )
        
        # Publish event for reputation/notification
        publish_message_sent(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_id=message.id
        )
        
        return MessageResponse.model_validate(message)
    
    async def get_user_messages(
        self,
        db: AsyncSession,
        user_id: int,
        other_user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 50
    ) -> MessageListResponse:
        """
        Get messages for a user.
        
        Args:
            db: Database session
            user_id: ID of user
            other_user_id: Optional filter for specific conversation
            page: Page number
            page_size: Results per page
        
        Returns:
            Paginated message list
        """
        # Build query
        conditions = []
        
        if other_user_id:
            # Specific conversation
            conditions.append(
                or_(
                    and_(
                        Message.sender_id == user_id,
                        Message.recipient_id == other_user_id,
                        Message.is_deleted_by_sender == False
                    ),
                    and_(
                        Message.sender_id == other_user_id,
                        Message.recipient_id == user_id,
                        Message.is_deleted_by_recipient == False
                    )
                )
            )
        else:
            # All conversations
            conditions.append(
                or_(
                    and_(
                        Message.sender_id == user_id,
                        Message.is_deleted_by_sender == False
                    ),
                    and_(
                        Message.recipient_id == user_id,
                        Message.is_deleted_by_recipient == False
                    )
                )
            )
        
        # Count total
        count_query = select(func.count(Message.id)).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated messages
        offset = (page - 1) * page_size
        query = (
            select(Message)
            .where(and_(*conditions))
            .order_by(desc(Message.sent_at))
            .offset(offset)
            .limit(page_size)
        )
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return MessageListResponse(
            messages=[MessageResponse.model_validate(m) for m in messages],
            total=total,
            page=page,
            page_size=page_size,
            has_more=total > (page * page_size)
        )
    
    async def get_conversation_messages(
        self,
        db: AsyncSession,
        user_id: int,
        other_user_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> MessageListResponse:
        """
        Get messages in a specific conversation.
        
        Args:
            db: Database session
            user_id: ID of current user
            other_user_id: ID of other user in conversation
            page: Page number
            page_size: Results per page
        
        Returns:
            Paginated message list
        """
        return await self.get_user_messages(
            db=db,
            user_id=user_id,
            other_user_id=other_user_id,
            page=page,
            page_size=page_size
        )
    
    async def mark_as_read(
        self,
        db: AsyncSession,
        user_id: int,
        message_ids: List[int]
    ) -> int:
        """
        Mark messages as read.
        
        Args:
            db: Database session
            user_id: ID of user (must be recipient)
            message_ids: List of message IDs to mark
        
        Returns:
            Number of messages marked as read
        """
        # Get messages where user is recipient and not yet read
        result = await db.execute(
            select(Message).where(
                and_(
                    Message.id.in_(message_ids),
                    Message.recipient_id == user_id,
                    Message.status != MessageStatus.READ
                )
            )
        )
        messages = result.scalars().all()
        
        count = 0
        now = datetime.utcnow()
        
        for message in messages:
            message.status = MessageStatus.READ
            message.read_at = now
            count += 1
        
        if count > 0:
            await db.flush()
            
            # Update conversation unread counts
            # Group by sender to batch update
            senders = set(m.sender_id for m in messages)
            for sender_id in senders:
                await self._decrement_unread_count(db, user_id, sender_id, count)
        
        return count
    
    async def mark_conversation_as_read(
        self,
        db: AsyncSession,
        user_id: int,
        other_user_id: int
    ) -> int:
        """
        Mark all messages in a conversation as read.
        
        Args:
            db: Database session
            user_id: ID of current user
            other_user_id: ID of other user
        
        Returns:
            Number of messages marked as read
        """
        # Get all unread messages from other user
        result = await db.execute(
            select(Message).where(
                and_(
                    Message.sender_id == other_user_id,
                    Message.recipient_id == user_id,
                    Message.status != MessageStatus.READ
                )
            )
        )
        messages = result.scalars().all()
        
        if not messages:
            return 0
        
        now = datetime.utcnow()
        for message in messages:
            message.status = MessageStatus.READ
            message.read_at = now
        
        await db.flush()
        
        # Reset unread count in conversation
        await self._reset_unread_count(db, user_id, other_user_id)
        
        return len(messages)
    
    async def delete_message(
        self,
        db: AsyncSession,
        user_id: int,
        message_id: int
    ) -> bool:
        """
        Soft delete a message (for current user only).
        
        Args:
            db: Database session
            user_id: ID of user deleting
            message_id: ID of message to delete
        
        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()
        
        if not message:
            return False
        
        # Check user is sender or recipient
        if message.sender_id == user_id:
            message.is_deleted_by_sender = True
        elif message.recipient_id == user_id:
            message.is_deleted_by_recipient = True
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete message you're not part of"
            )
        
        await db.flush()
        return True
    
    async def get_conversations(
        self,
        db: AsyncSession,
        user_id: int
    ) -> ConversationListResponse:
        """
        Get all conversations for a user.
        
        Args:
            db: Database session
            user_id: ID of user
        
        Returns:
            List of conversation previews
        """
        # Get conversations involving user
        result = await db.execute(
            select(Conversation)
            .options(
                selectinload(Conversation.user1),
                selectinload(Conversation.user2),
                selectinload(Conversation.last_message)
            )
            .where(
                or_(
                    Conversation.user1_id == user_id,
                    Conversation.user2_id == user_id
                )
            )
            .order_by(desc(Conversation.last_message_at))
        )
        conversations = result.scalars().all()
        
        previews = []
        total_unread = 0
        
        for conv in conversations:
            # Determine other user and unread count
            if conv.user1_id == user_id:
                other_user = conv.user2
                unread_count = conv.unread_count_user1
            else:
                other_user = conv.user1
                unread_count = conv.unread_count_user2
            
            total_unread += unread_count
            
            preview = ConversationPreview(
                conversation_id=conv.id,
                other_user_id=other_user.id,
                other_user_name=other_user.profile.name if other_user.profile else "Unknown",
                last_message_content=(
                    conv.last_message.content[:100] if conv.last_message else None
                ),
                last_message_at=conv.last_message_at,
                unread_count=unread_count,
                created_at=conv.created_at
            )
            previews.append(preview)
        
        return ConversationListResponse(
            conversations=previews,
            total=len(previews),
            unread_total=total_unread
        )
    
    async def get_unread_count(
        self,
        db: AsyncSession,
        user_id: int
    ) -> UnreadCountResponse:
        """
        Get total unread message count for user.
        
        Args:
            db: Database session
            user_id: ID of user
        
        Returns:
            Unread count info
        """
        # Get conversations
        result = await db.execute(
            select(Conversation).where(
                or_(
                    Conversation.user1_id == user_id,
                    Conversation.user2_id == user_id
                )
            )
        )
        conversations = result.scalars().all()
        
        total_unread = 0
        conversations_with_unread = 0
        
        for conv in conversations:
            if conv.user1_id == user_id:
                unread = conv.unread_count_user1
            else:
                unread = conv.unread_count_user2
            
            if unread > 0:
                conversations_with_unread += 1
                total_unread += unread
        
        return UnreadCountResponse(
            unread_count=total_unread,
            conversations_with_unread=conversations_with_unread
        )
    
    async def _update_conversation(
        self,
        db: AsyncSession,
        user1_id: int,
        user2_id: int,
        message_id: int,
        message_time: datetime
    ):
        """Update or create conversation metadata."""
        # Ensure user1_id < user2_id for consistency
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        # Get or create conversation
        result = await db.execute(
            select(Conversation).where(
                and_(
                    Conversation.user1_id == user1_id,
                    Conversation.user2_id == user2_id
                )
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            conversation = Conversation(
                user1_id=user1_id,
                user2_id=user2_id,
                last_message_id=message_id,
                last_message_at=message_time,
                unread_count_user1=0,
                unread_count_user2=0
            )
            db.add(conversation)
        else:
            conversation.last_message_id = message_id
            conversation.last_message_at = message_time
        
        # Increment unread count for recipient
        # If sender is user1, increment user2's count, and vice versa
        result = await db.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one()
        
        if message.recipient_id == user1_id:
            conversation.unread_count_user1 += 1
        else:
            conversation.unread_count_user2 += 1
        
        await db.flush()
    
    async def _decrement_unread_count(
        self,
        db: AsyncSession,
        user_id: int,
        other_user_id: int,
        count: int
    ):
        """Decrement unread count in conversation."""
        user1_id, user2_id = sorted([user_id, other_user_id])
        
        result = await db.execute(
            select(Conversation).where(
                and_(
                    Conversation.user1_id == user1_id,
                    Conversation.user2_id == user2_id
                )
            )
        )
        conversation = result.scalar_one_or_none()
        
        if conversation:
            if user_id == user1_id:
                conversation.unread_count_user1 = max(0, conversation.unread_count_user1 - count)
            else:
                conversation.unread_count_user2 = max(0, conversation.unread_count_user2 - count)
            await db.flush()
    
    async def _reset_unread_count(
        self,
        db: AsyncSession,
        user_id: int,
        other_user_id: int
    ):
        """Reset unread count to zero."""
        user1_id, user2_id = sorted([user_id, other_user_id])
        
        result = await db.execute(
            select(Conversation).where(
                and_(
                    Conversation.user1_id == user1_id,
                    Conversation.user2_id == user2_id
                )
            )
        )
        conversation = result.scalar_one_or_none()
        
        if conversation:
            if user_id == user1_id:
                conversation.unread_count_user1 = 0
            else:
                conversation.unread_count_user2 = 0
            await db.flush()