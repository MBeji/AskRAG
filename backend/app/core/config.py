"""
Configuration settings for AskRAG application.
Uses Pydantic BaseSettings for robust environment variable management.
"""

import json
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Explicitly load .env file here if not relying on BaseSettings finding it,
# or if you need variables loaded before Settings class definition for some reason.
# load_dotenv() # BaseSettings with env_file in model_config should handle this.

class Settings(BaseSettings):
    """Application settings, loaded from environment variables and .env files."""
    
    # Application
    PROJECT_NAME: str = "AskRAG API"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    
    # Environment: development, production, staging
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "askrag_dev"
    
    # OpenAI API Key - Essential for RAG
    OPENAI_API_KEY: Optional[str] = None
    EMBEDDING_MODEL_NAME: str = "text-embedding-ada-002" # Default OpenAI embedding model

    # Text Splitting Configuration
    TEXT_CHUNK_SIZE: int = 1000
    TEXT_CHUNK_OVERLAP: int = 200

    # FAISS Vector Store Configuration
    FAISS_INDEX_PATH: str = "faiss_indexes/askrag.index" # Relative to app root or an absolute path
    FAISS_INDEX_DIMENSION: int = 1536 # Dimension for text-embedding-ada-002 / text-embedding-3-small

    # RAG / Search Configuration
    SEARCH_TOP_K: int = 5 # Number of relevant chunks to retrieve

    # LLM Configuration
    LLM_MODEL_NAME: str = "gpt-3.5-turbo" # Default LLM model
    MAX_CONTEXT_TOKENS: int = 3000 # Max tokens for context passed to LLM
    LLM_TEMPERATURE: float = 0.7 # Temperature for LLM generation
    LLM_MAX_OUTPUT_TOKENS: int = 500 # Max tokens for LLM output

    # CORS - Expecting a comma-separated string from env, or a JSON string list
    BACKEND_CORS_ORIGINS_STR: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = True
    # TRUSTED_HOSTS_STR: str = "localhost,127.0.0.1,0.0.0.0" # Example
    
    # Session
    SESSION_SECRET_KEY: str = "session-secret-key-change-in-production"
    SESSION_COOKIE_NAME: str = "askrag_session"
    SESSION_MAX_AGE: int = 86400  # 24 hours

    # Email (for password reset) - Optional fields allow them to be unset
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None # Defaults to PROJECT_NAME if None
    
    # Feature Flags
    FEATURE_REGISTRATION: bool = True
    FEATURE_PASSWORD_RESET: bool = True
    FEATURE_EMAIL_VERIFICATION: bool = False
    FEATURE_ADMIN_PANEL: bool = True
    
    # Upload settings
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS_STR: str = "pdf,txt,docx,md"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Rate Limiting Defaults
    DEFAULT_RATE_LIMIT: str = "100/hour"  # Default limit for all routes
    AUTH_RATE_LIMIT: str = "10/minute"     # Stricter limit for login/register
    HEALTH_CHECK_RATE_LIMIT: str = "20/minute" # Limit for health checks

    # Computed properties or validators
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        if not self.BACKEND_CORS_ORIGINS_STR:
            return []
        if self.BACKEND_CORS_ORIGINS_STR.startswith("[") and self.BACKEND_CORS_ORIGINS_STR.endswith("]"):
            try:
                return json.loads(self.BACKEND_CORS_ORIGINS_STR)
            except json.JSONDecodeError:
                pass # Fall through to comma-separated logic
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS_STR.split(",")]

    @property
    def ALLOWED_EXTENSIONS(self) -> List[str]:
        if not self.ALLOWED_EXTENSIONS_STR:
            return []
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS_STR.split(",")]

    @property
    def DATABASE_URL(self) -> str:
        return f"{self.MONGODB_URL}/{self.MONGODB_DATABASE}"

    @property
    def EMAILS_FROM_NAME_EFFECTIVE(self) -> str:
        return self.EMAILS_FROM_NAME or self.PROJECT_NAME
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT == "staging"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False # Env var names are case-insensitive by default with BaseSettings
    )

# Global settings instance
settings = Settings()
load_dotenv(settings.model_config.get("env_file")) # Ensure .env is loaded if BaseSettings doesn't do it early enough
# settings = Settings(_env_file=os.getenv('ENV_FILE', '.env')) # Another way if specific .env is needed