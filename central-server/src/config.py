from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CORS_ORIGINS: list = ["http://localhost:8080"]  # Vue.js client
    MAX_WS_MESSAGE_SIZE: int = 100 * 1024 * 1024  # 100MB for video frames

settings = Settings()