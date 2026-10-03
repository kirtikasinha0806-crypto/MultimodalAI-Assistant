import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

# Explicitly load .env with absolute path so it works regardless of working directory
BACKEND_DIR = Path(__file__).resolve().parent.parent
env_file_path = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=env_file_path, override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Multimodal AI Personal Assistant"
    API_V1_STR: str = "/api/v1"
    
    # Gemini AI configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PRIMARY_MODEL: str = os.getenv("PRIMARY_MODEL", "gemini-3.8-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
    EMBEDDING_DIMENSION: int = 3072
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/chatbot"
    )
    
    # File storage
    UPLOAD_DIR: str = str(BACKEND_DIR / "uploads")
    AUDIO_DIR: str = str(BACKEND_DIR / "audio_cache")
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: list[str] = [
        ".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".json", 
        ".xlsx", ".xls", ".pptx", ".ppt", ".py", ".js", ".ts", 
        ".html", ".css", ".xml", ".yaml", ".yml", ".rtf", ".log"
    ]
    ALLOWED_IMAGE_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png", ".webp", ".gif"]
    ALLOWED_AUDIO_EXTENSIONS: list[str] = [".mp3", ".wav", ".m4a", ".ogg", ".webm"]
    
    # RAG settings
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100
    TOP_K_CHUNKS: int = 4
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3001"]

    class Config:
        env_file = str(env_file_path)
        extra = "ignore"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.AUDIO_DIR, exist_ok=True)
