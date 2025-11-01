from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

# Get the backend directory (where .env should be)
BACKEND_DIR = Path(__file__).parent.parent.parent

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
    
    # Calendly - THIS IS CRITICAL
    calendly_api_key: str = ""
    calendly_base_url: str = "https://api.calendly.com"
    
    # Data
    data_dir: Path = BACKEND_DIR / "calendly_dump"
    
    # Redis (for caching)
    redis_url: str = "redis://localhost:6379"
    
    # Database
    database_url: str = "sqlite:///./calendly_analytics.db"
    
    class Config:
        # Look for .env in the backend directory
        env_file = str(BACKEND_DIR / ".env")
        case_sensitive = False
        extra = "allow"

_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        
        # Print configuration for debugging
        print("\n" + "="*70)
        print("Configuration Loaded:")
        print("="*70)
        print(f"Backend Directory: {BACKEND_DIR}")
        print(f"Data Directory: {_settings.data_dir}")
        print(f"Calendly API Key Set: {'Yes' if _settings.calendly_api_key else 'No'}")
        if _settings.calendly_api_key:
            print(f"Calendly API Key (first 10 chars): {_settings.calendly_api_key[:10]}...")
        print("="*70 + "\n")
        
        # Ensure data directory exists
        _settings.data_dir.mkdir(parents=True, exist_ok=True)
        
    return _settings