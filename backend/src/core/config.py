"""Application configuration settings."""
import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseModel, Field, validator
from pydantic_settings import BaseSettings
from typing import Any, Dict, List, Optional, Union


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Application
    APP_NAME: str = Field("Stock Analysis System", env="APP_NAME")
    APP_VERSION: str = Field("1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(True, env="DEBUG")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")

    # Server
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    RELOAD: bool = Field(False, env="RELOAD")
    LOG_LEVEL: str = Field("info", env="LOG_LEVEL")

    # Security
    SECRET_KEY: str = Field("test-secret-key-for-development", env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Database
    DATABASE_URL: str = Field("sqlite:///./test.db", env="DATABASE_URL")
    DB_HOST: str = Field("localhost", env="DB_HOST")
    DB_PORT: int = Field(5432, env="DB_PORT")
    DB_NAME: str = Field("stock_analysis", env="DB_NAME")
    DB_USER: str = Field("stock_user", env="DB_USER")
    DB_PASSWORD: str = Field("password", env="DB_PASSWORD")
    DB_POOL_SIZE: int = Field(5, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(10, env="DB_MAX_OVERFLOW")

    # Database URL validator removed for simplicity in testing

    # Redis
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")

    # Celery
    CELERY_BROKER_URL: str = Field("redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(
        "redis://localhost:6379/2", env="CELERY_RESULT_BACKEND"
    )
    CELERY_TASK_SERIALIZER: str = Field("json", env="CELERY_TASK_SERIALIZER")
    CELERY_RESULT_SERIALIZER: str = Field("json", env="CELERY_RESULT_SERIALIZER")
    CELERY_ACCEPT_CONTENT: List[str] = Field(["json"], env="CELERY_ACCEPT_CONTENT")
    CELERY_TIMEZONE: str = Field("Asia/Taipei", env="CELERY_TIMEZONE")

    # Stock APIs
    ALPHA_VANTAGE_API_KEY: Optional[str] = Field(None, env="ALPHA_VANTAGE_API_KEY")
    YAHOO_FINANCE_ENABLED: bool = Field(True, env="YAHOO_FINANCE_ENABLED")
    FINNHUB_API_KEY: Optional[str] = Field(None, env="FINNHUB_API_KEY")

    # Technical Analysis
    DEFAULT_STOCK_SYMBOLS: List[str] = Field(
        ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"], env="DEFAULT_STOCK_SYMBOLS"
    )
    DATA_UPDATE_INTERVAL_MINUTES: int = Field(60, env="DATA_UPDATE_INTERVAL_MINUTES")
    ANALYSIS_LOOKBACK_DAYS: int = Field(252, env="ANALYSIS_LOOKBACK_DAYS")

    # Stock symbols validator removed for simplicity

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(100, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(200, env="RATE_LIMIT_BURST")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    CORS_ALLOW_METHODS: List[str] = Field(
        ["GET", "POST", "PUT", "DELETE", "OPTIONS"], env="CORS_ALLOW_METHODS"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(["*"], env="CORS_ALLOW_HEADERS")

    # CORS origins validator removed for simplicity

    # Logging
    LOG_FORMAT: str = Field("json", env="LOG_FORMAT")
    LOG_FILE_PATH: str = Field("logs/app.log", env="LOG_FILE_PATH")
    LOG_ROTATION_SIZE: str = Field("10MB", env="LOG_ROTATION_SIZE")
    LOG_BACKUP_COUNT: int = Field(5, env="LOG_BACKUP_COUNT")

    # Background Tasks
    ENABLE_SCHEDULED_TASKS: bool = Field(True, env="ENABLE_SCHEDULED_TASKS")
    MARKET_DATA_UPDATE_SCHEDULE: str = Field("0 9 * * 1-5", env="MARKET_DATA_UPDATE_SCHEDULE")
    TECHNICAL_ANALYSIS_SCHEDULE: str = Field("0 18 * * 1-5", env="TECHNICAL_ANALYSIS_SCHEDULE")

    # File Storage
    UPLOAD_DIR: str = Field("uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE_MB: int = Field(10, env="MAX_FILE_SIZE_MB")
    ALLOWED_FILE_EXTENSIONS: List[str] = Field(
        ["csv", "xlsx", "json"], env="ALLOWED_FILE_EXTENSIONS"
    )

    # File extensions validator removed for simplicity

    # Health Checks & Monitoring
    HEALTH_CHECK_ENABLED: bool = Field(True, env="HEALTH_CHECK_ENABLED")
    METRICS_ENABLED: bool = Field(True, env="METRICS_ENABLED")
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")

    # Testing
    TEST_DATABASE_URL: Optional[str] = Field(None, env="TEST_DATABASE_URL")
    TEST_REDIS_URL: str = Field("redis://localhost:6379/15", env="TEST_REDIS_URL")

    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @validator('CORS_ALLOW_METHODS', pre=True)
    def parse_cors_methods(cls, v):
        """Parse CORS methods from comma-separated string."""
        if isinstance(v, str):
            return [method.strip() for method in v.split(',') if method.strip()]
        return v

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# Create global settings instance
settings = Settings()

# For testing
def get_settings() -> Settings:
    """Get settings instance."""
    return settings