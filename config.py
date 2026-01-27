"""
Application configuration using Pydantic Settings.
Environment-based configuration for all services.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    app_name: str = "Roommate Finder API"
    debug: bool = False
    api_version: str = "v1"
    
    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/roommate_db"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600  # 1 hour
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # Password
    bcrypt_rounds: int = 12
    
    # Matching Engine
    matching_version: str = "v1"
    matching_max_distance_km: float = 50.0
    matching_min_score_threshold: int = 30
    matching_default_limit: int = 20
    
    # Rate Limiting
    rate_limit_messages_per_hour: int = 50
    rate_limit_match_requests_per_day: int = 100
    
    # Reputation
    reputation_initial_score: int = 100
    reputation_ghosting_penalty: int = -10
    reputation_spam_penalty: int = -5
    reputation_min_score: int = 0
    reputation_max_score: int = 100
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Location
    location_search_radius_km: float = 50.0


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()