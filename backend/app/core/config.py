"""
Watchout Backend - Core Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Watchout"
    app_env: str = "development"
    app_secret_key: str = "change-this-in-production"
    frontend_url: str = "http://localhost:3000"
    dev_bypass_secret: Optional[str] = None  # Must be set in .env to enable
    
    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "watchout"
    
    # Firebase
    firebase_project_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""
    
    # Groq AI
    groq_api_key: str = ""
    groq_main_model: str = "llama-3.3-70b-versatile"  # Main reasoning + itinerary generation
    groq_fast_model: str = "llama3-8b-8192"  # Fast UI + small tasks
    
    # Google Places
    google_places_api_key: str = ""
    
    # Mapbox
    mapbox_access_token: str = ""
    
    # Weather API
    weatherapi_key: str = ""
    
    # Search APIs
    tavily_api_key: str = ""
    serper_api_key: str = ""
    
    # Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
