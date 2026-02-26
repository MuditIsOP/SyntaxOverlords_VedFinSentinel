import os
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from typing import ClassVar, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "VedFin Sentinel"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security — SECRET_KEY auto-generates if not set; set via env in production
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_hex(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database — PostgreSQL is primary (per PRD), SQLite as local dev fallback
    DATABASE_URL: str = "postgresql+asyncpg://sentinel:vedfin_secure_password@localhost:5432/sentinel"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ML Models
    MODEL_PATH: str = "./ml/artifacts/sentinel_ensemble.pkl"
    SHAP_BACKGROUND_SAMPLES: int = 100
    VEDIC_BENCHMARK_ENABLED: bool = True
    
    # Ensemble configuration — weights must sum to 1.0
    ENSEMBLE_XGB_WEIGHT: float = Field(default=0.7, ge=0.0, le=1.0)
    ENSEMBLE_ISO_WEIGHT: float = Field(default=0.3, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_ensemble_weights(self):
        total = self.ENSEMBLE_XGB_WEIGHT + self.ENSEMBLE_ISO_WEIGHT
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Ensemble weights must sum to 1.0, got {total}")
        return self
    
    # CORS — configurable via environment
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=[".env", ".env.local"], 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore",
        validate_assignment=True
    )

settings = Settings()
