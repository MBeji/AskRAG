"""
Configuration settings for AskRAG application.
Simplified configuration for Pydantic v1 compatibility.
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings."""
    
    # Application
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "AskRAG API")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days
    
    # Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "askrag_dev")
    DATABASE_URL: str = f"{MONGODB_URL}/{MONGODB_DATABASE}"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173"
    ]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
    
    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    TRUSTED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # Session
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "session-secret-key-change-in-production")
    SESSION_COOKIE_NAME: str = os.getenv("SESSION_COOKIE_NAME", "askrag_session")
    SESSION_MAX_AGE: int = int(os.getenv("SESSION_MAX_AGE", "86400"))  # 24 hours
    
    # Email (for password reset)
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() == "true"
    SMTP_PORT: Optional[int] = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: Optional[str] = os.getenv("EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: Optional[str] = os.getenv("EMAILS_FROM_NAME", PROJECT_NAME)
    
    # Feature Flags
    FEATURE_REGISTRATION: bool = os.getenv("FEATURE_REGISTRATION", "true").lower() == "true"
    FEATURE_PASSWORD_RESET: bool = os.getenv("FEATURE_PASSWORD_RESET", "true").lower() == "true"
    FEATURE_EMAIL_VERIFICATION: bool = os.getenv("FEATURE_EMAIL_VERIFICATION", "false").lower() == "true"
    FEATURE_ADMIN_PANEL: bool = os.getenv("FEATURE_ADMIN_PANEL", "true").lower() == "true"
    
    # Upload settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "txt", "docx", "md"]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging mode"""
        return self.ENVIRONMENT == "staging"


# Global settings instance
settings = Settings()