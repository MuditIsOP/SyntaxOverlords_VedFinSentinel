import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import ClassVar

class Settings(BaseSettings):
    PROJECT_NAME: str = "VedFin Sentinel"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "super_secret_for_local_testing"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database — PostgreSQL is primary (per PRD), SQLite as local dev fallback
    DATABASE_URL: str = "postgresql+asyncpg://sentinel:vedfin_secure_password@localhost:5432/sentinel"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ML Models
    MODEL_PATH: str = "./ml/artifacts/sentinel_ensemble.pkl"
    SHAP_BACKGROUND_SAMPLES: int = 100
    VEDIC_BENCHMARK_ENABLED: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
