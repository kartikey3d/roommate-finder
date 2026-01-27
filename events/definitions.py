"""
Event definitions and publisher for event-driven architecture.
Events trigger Celery workers for async processing.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict
import json


class EventType(str, Enum):
    """Types of domain events."""
    PROFILE_UPDATED = "profile_updated"
    PREFERENCES_UPDATED = "preferences_updated"
    LISTING_CREATED = "listing_created"
    LISTING_UPDATED = "listing_updated"
    MATCH_REQUESTED = "match_requested"
    MESSAGE_SENT = "message_sent"
    REPORT_FILED = "report_filed"
    USER_GHOSTED = "user_ghosted"


@dataclass
class DomainEvent:
    """Base domain event."""
    event_type: EventType
    user_id: int
    timestamp: datetime
    data: Dict[str, Any]
    
    def to_dict(self) -> dict:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class EventPublisher:
    """
    Event publisher - sends events to Celery workers.
    
    In production, this would publish to a message queue (Redis/RabbitMQ).
    For now, directly invokes Celery tasks.
    """
    
    def __init__(self):
        # Import here to avoid circular dependencies
        from workers.tasks import (
            handle_profile_updated,
            handle_preferences_updated,
            handle_listing_created,
            handle_message_sent
        )
        
        self.handlers = {
            EventType.PROFILE_UPDATED: handle_profile_updated,
            EventType.PREFERENCES_UPDATED: handle_preferences_updated,
            EventType.LISTING_CREATED: handle_listing_created,
            EventType.MESSAGE_SENT: handle_message_sent,
        }
    
    def publish(self, event: DomainEvent):
        """
        Publish event to appropriate handler.
        
        This triggers async Celery task.
        """
        handler = self.handlers.get(event.event_type)
        if handler:
            # Call Celery task asynchronously
            handler.delay(event.to_dict())
        else:
            # Log unhandled event type
            print(f"No handler for event type: {event.event_type}")


# Global publisher instance
event_publisher = EventPublisher()


def publish_profile_updated(user_id: int, changes: Dict[str, Any]):
    """Publish profile updated event."""
    event = DomainEvent(
        event_type=EventType.PROFILE_UPDATED,
        user_id=user_id,
        timestamp=datetime.utcnow(),
        data={"changes": changes}
    )
    event_publisher.publish(event)


def publish_preferences_updated(user_id: int, changes: Dict[str, Any]):
    """Publish preferences updated event."""
    event = DomainEvent(
        event_type=EventType.PREFERENCES_UPDATED,
        user_id=user_id,
        timestamp=datetime.utcnow(),
        data={"changes": changes}
    )
    event_publisher.publish(event)


def publish_listing_created(user_id: int, listing_id: int):
    """Publish listing created event."""
    event = DomainEvent(
        event_type=EventType.LISTING_CREATED,
        user_id=user_id,
        timestamp=datetime.utcnow(),
        data={"listing_id": listing_id}
    )
    event_publisher.publish(event)


def publish_message_sent(sender_id: int, recipient_id: int, message_id: int):
    """Publish message sent event."""
    event = DomainEvent(
        event_type=EventType.MESSAGE_SENT,
        user_id=sender_id,
        timestamp=datetime.utcnow(),
        data={
            "recipient_id": recipient_id,
            "message_id": message_id
        }
    )
    event_publisher.publish(event)