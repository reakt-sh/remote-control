from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CORS_ORIGINS: list = [
        "http://localhost:8080",
        "https://209.38.218.207:8080"]
    MAX_WS_MESSAGE_SIZE: int = 100 * 1024 * 1024  # 100MB for video frames

settings = Settings()