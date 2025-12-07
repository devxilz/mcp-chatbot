from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "MCPChatbot"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

     # Base data directory
    DATA_DIR: str = "data"

    # Sub-directories
    MEMORY_STORE_DIR: str = "data/memory_store"
    PROFILE_STORE_DIR: str = "data/profile_store"

    # Actual database file locations
    SESSION_DB_PATH: str = "data/memory_store/memory_session.db"
    PROFILE_DB_PATH: str = "data/profile_store/user_profile.db"

    OPENAI_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
