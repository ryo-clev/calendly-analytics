"""
Configuration module - Fixed to handle data directory correctly
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

# Get the project root directory (parent of backend)
BACKEND_DIR = Path(__file__).parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

class Settings(BaseSettings):
    """Application settings with proper path handling."""
    
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
    
    # Calendly - CRITICAL
    calendly_api_key: str = ""
    calendly_base_url: str = "https://api.calendly.com"
    
    # Data directory - FIXED to use absolute path
    data_dir: Path = PROJECT_ROOT / "calendly_dump"
    
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
    """
    Get or create settings singleton.
    Ensures data directory is properly resolved and created.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        
        # Resolve data_dir to absolute path if it's relative
        if not _settings.data_dir.is_absolute():
            _settings.data_dir = PROJECT_ROOT / _settings.data_dir
        
        # Ensure data directory exists
        _settings.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Print configuration for debugging
        print("\n" + "=" * 70)
        print("Configuration Loaded:")
        print("=" * 70)
        print(f"Project Root: {PROJECT_ROOT}")
        print(f"Backend Directory: {BACKEND_DIR}")
        print(f"Data Directory: {_settings.data_dir}")
        print(f"Data Directory Exists: {_settings.data_dir.exists()}")
        print(f"Calendly API Key Set: {'Yes' if _settings.calendly_api_key else 'No'}")
        if _settings.calendly_api_key and _settings.calendly_api_key != "your_calendly_api_key_here":
            print(f"Calendly API Key (first 10 chars): {_settings.calendly_api_key[:10]}...")
        print("=" * 70 + "\n")
        
    return _settings