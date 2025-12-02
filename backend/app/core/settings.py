from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "MCPChatbot"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    DATA_DIR: str = "backend/data"
    MEMORY_STORE: str = "backend/data/memory_store"
    USER_SESSIONS: str = "backend/data/user_sessions"

    OPENAI_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
