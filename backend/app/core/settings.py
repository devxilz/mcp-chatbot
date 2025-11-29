from pydantic_settings import BaseSettings
from functools import lru_cache


# ============================================================
# APPLICATION SETTINGS MODEL
#
# Purpose:
# - Central place to store all configurable values
# - Automatically loads values from environment variables
# - Useful for production, staging, and local dev configs
#
# BaseSettings automatically:
# - Reads from environment variables
# - Validates types
# - Merges values from .env file if Config.env_file is set
# ============================================================
class Settings(BaseSettings):
    # Basic application metadata
    APP_NAME: str = "MCPChatbot"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True  # Enables debug-friendly behavior

    # Project directory structure for memory, sessions, etc.
    DATA_DIR: str = "backend/data"
    MEMORY_STORE: str = "backend/data/memory_store"
    USER_SESSIONS: str = "backend/data/user_sessions"

    # API keys (None by default so app does not crash if missing)
    OPENAI_API_KEY: str | None = None

    # Pydantic Settings configuration
    class Config:
        # Load environment variables from .env file automatically
        env_file = ".env"
        env_file_encoding = "utf-8"


# ============================================================
# SETTINGS PROVIDER (Singleton via lru_cache)
#
# Why use @lru_cache?
# - Ensures Settings() is created only once
# - Prevents re-reading the .env file or environment repeatedly
# - Improves performance and behaves like a global configuration
#
# get_settings() is imported anywhere across the project to get
# a single shared Settings instance with validated values.
# ============================================================
@lru_cache
def get_settings() -> Settings:
    return Settings()
