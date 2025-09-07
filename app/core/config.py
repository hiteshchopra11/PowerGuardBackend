"""Application configuration."""

import os
from typing import Optional


class Settings:
    """Application settings."""
    
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    DATABASE_URL: str = "sqlite:///./power_guard.db"
    
    # Rate limiting settings
    MAX_RETRIES: int = 5
    INITIAL_RETRY_DELAY: int = 2
    MAX_RETRY_DELAY: int = 120
    
    # Actionable types
    ALLOWED_ACTIONABLE_TYPES = {
        "SET_STANDBY_BUCKET",
        "RESTRICT_BACKGROUND_DATA", 
        "KILL_APP",
        "MANAGE_WAKE_LOCKS",
        "THROTTLE_CPU_USAGE"
    }
    
    ACTIONABLE_TYPE_DESCRIPTIONS = {
        1: "SET_STANDBY_BUCKET",
        2: "RESTRICT_BACKGROUND_DATA",
        3: "KILL_APP",
        4: "MANAGE_WAKE_LOCKS", 
        5: "THROTTLE_CPU_USAGE"
    }


settings = Settings()