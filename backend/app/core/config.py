from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Calendly Analytics"
    version: str = "1.0.0"
    description: str = "FAANG-grade analytics platform for Calendly data"
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]
    
    # Calendly
    calendly_api_key: str
    calendly_base_url: str = "https://api.calendly.com"
    
    # Data
    data_dir: Path = Path("./calendly_dump")
    
    # Redis (for caching)
    redis_url: str = "redis://localhost:6379"
    
    # Database
    database_url: str = "sqlite:///./calendly_analytics.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

def get_settings() -> Settings:
    return Settings()