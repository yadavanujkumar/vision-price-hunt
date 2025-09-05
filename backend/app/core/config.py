from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    app_name: str = "Vision Price Hunt"
    debug: bool = True
    
    # API Settings
    api_v1_str: str = "/api/v1"
    
    # CORS Settings
    backend_cors_origins: List[str] = ["http://localhost:3000"]
    
    # Upload Settings
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".webp"]
    upload_dir: str = "uploads"
    
    # Vision Service Settings
    ocr_confidence_threshold: float = 0.5
    similarity_threshold: float = 0.7
    max_similar_products: int = 10
    
    # Scraper Settings
    request_timeout: int = 30
    max_retries: int = 3
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    class Config:
        env_file = ".env"

settings = Settings()