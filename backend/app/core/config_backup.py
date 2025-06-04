"""
Configuration settings for AskRAG application.
Enhanced environment variable management for Étape 6.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseModel):
    """Application settings with comprehensive environment support."""
    
    # Application
    PROJECT_NAME: str = "AskRAG API"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Security & Authentication
    SECRET_KEY: str = "dev-secret-key-change-in-production-2024"
    JWT_SECRET_KEY: str = "jwt-dev-secret-key-change-in-production-2024"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "askrag"
    MONGODB_TEST_DB_NAME: str = "askrag_test"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".docx", ".md", ".rtf"]
    TEMP_DIR: str = "./temp"
    
    # Vector Database (FAISS)
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    VECTOR_DIMENSION: int = 1536
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # RAG Configuration
    DEFAULT_TOP_K: int = 5
    DEFAULT_TEMPERATURE: float = 0.7
    MAX_SEARCH_RESULTS: int = 10
    SIMILARITY_THRESHOLD: float = 0.7
    
    # Redis (Cache & Sessions)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_TTL: int = 3600
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def assemble_extensions(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    # Logging
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "./logs/askrag.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Health Check
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_CHECK_TIMEOUT: int = 10
    
    # Feature Flags
    ENABLE_CHAT: bool = True
    ENABLE_DOCUMENT_UPLOAD: bool = True
    ENABLE_VECTOR_SEARCH: bool = True
    ENABLE_USER_REGISTRATION: bool = True
    ENABLE_ADMIN_PANEL: bool = False
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    PROMETHEUS_METRICS: bool = True
    
    # Email (for notifications)
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    
    # External Services
    SENTRY_DSN: str = ""
    DATADOG_API_KEY: str = ""
    
    # SSL & Security (for production)
    SSL_VERIFY: bool = True
    SECURE_SSL_REDIRECT: bool = False
    SECURE_HSTS_SECONDS: int = 0
    SECURE_CONTENT_TYPE_NOSNIFF: bool = True
    SECURE_BROWSER_XSS_FILTER: bool = True
    
    # Performance
    WORKER_CONNECTIONS: int = 1000
    WORKER_TIMEOUT: int = 30
    KEEP_ALIVE: int = 2
    
    @computed_field
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT.lower() == "development"
    
    @computed_field
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT.lower() == "production"
    
    @computed_field
    @property
    def is_staging(self) -> bool:
        """Check if running in staging mode"""
        return self.ENVIRONMENT.lower() == "staging"
      
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Create settings instance
settings = Settings()
