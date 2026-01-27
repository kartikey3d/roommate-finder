"""
Celery workers for background task processing.
Handles async operations triggered by domain events.
"""
from celery import Celery
from typing import Dict, Any
import asyncio

from config import get_settings


settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "roommate_finder",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)


def run_async(coro):
    """Helper to run async functions in Celery tasks."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


@celery_app.task(name="handle_profile_updated")
def handle_profile_updated(event_data: Dict[str, Any]):
    """
    Handle profile updated event.
    
    Actions:
    - Recompute matches for user
    - Invalidate cached matches
    - Update derived signals
    """
    user_id = event_data["user_id"]
    changes = event_data["data"]["changes"]
    
    # TODO: Implement async recomputation
    print(f"Recomputing matches for user {user_id} after profile update")
    print(f"Changes: {changes}")
    
    # This would call MatchingService to recompute
    # Store results in cache/DB for fast retrieval
    
    return {"status": "completed", "user_id": user_id}


@celery_app.task(name="handle_preferences_updated")
def handle_preferences_updated(event_data: Dict[str, Any]):
    """
    Handle preferences updated event.
    
    Actions:
    - Recompute matches for user
    - Invalidate cached matches
    """
    user_id = event_data["user_id"]
    changes = event_data["data"]["changes"]
    
    print(f"Recomputing matches for user {user_id} after preferences update")
    print(f"Changes: {changes}")
    
    return {"status": "completed", "user_id": user_id}


@celery_app.task(name="handle_listing_created")
def handle_listing_created(event_data: Dict[str, Any]):
    """
    Handle listing created event.
    
    Actions:
    - Update user's match rankings
    - Notify potential matches
    """
    user_id = event_data["user_id"]
    listing_id = event_data["data"]["listing_id"]
    
    print(f"Processing new listing {listing_id} for user {user_id}")
    
    return {"status": "completed", "listing_id": listing_id}


@celery_app.task(name="handle_message_sent")
def handle_message_sent(event_data: Dict[str, Any]):
    """
    Handle message sent event.
    
    Actions:
    - Update reputation signals
    - Check for spam patterns
    - Rate limit tracking
    """
    sender_id = event_data["user_id"]
    recipient_id = event_data["data"]["recipient_id"]
    message_id = event_data["data"]["message_id"]
    
    print(f"Processing message {message_id} from {sender_id} to {recipient_id}")
    
    # TODO: Implement spam detection
    # TODO: Update reputation signals
    
    return {"status": "completed", "message_id": message_id}


@celery_app.task(name="recompute_all_matches")
def recompute_all_matches():
    """
    Periodic task to recompute all matches.
    
    Run daily or when matching algorithm changes.
    """
    print("Starting batch match recomputation")
    
    # TODO: Implement batch processing
    # - Fetch all active users
    # - Recompute matches in batches
    # - Update cache/DB
    
    return {"status": "completed"}


@celery_app.task(name="update_reputation_scores")
def update_reputation_scores():
    """
    Periodic task to update reputation scores.
    
    Analyzes user behavior and adjusts scores.
    """
    print("Updating reputation scores")
    
    # TODO: Implement reputation updates
    # - Detect ghosting patterns
    # - Detect spam behavior
    # - Apply penalties/rewards
    
    return {"status": "completed"}


# Celery beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    "recompute-matches-daily": {
        "task": "recompute_all_matches",
        "schedule": 86400.0,  # Daily (in seconds)
    },
    "update-reputation-hourly": {
        "task": "update_reputation_scores",
        "schedule": 3600.0,  # Hourly
    },
}