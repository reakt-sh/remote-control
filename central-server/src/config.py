from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CORS_ORIGINS: list = [
        "http://localhost:8080",
        "https://localhost:8080",
        "http://209.38.218.207:8080",
        "https://209.38.218.207:8080",
        "http://rtsys-lab.de",
        "https://rtsys-lab.de",
        "http://www.rtsys-lab.de",
        "https://www.rtsys-lab.de"
        ]
    MAX_WS_MESSAGE_SIZE: int = 100 * 1024 * 1024  # 100MB for video frames

settings = Settings()
