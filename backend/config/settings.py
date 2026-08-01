"""
Central application configuration.
All environment-driven settings live here and are loaded once as a
cached singleton via `get_settings()`.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "Intelligent Answer Script Evaluation Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Security / JWT ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/aeval_db"
    )

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Storage ---
    STORAGE_BACKEND: str = "local"  # local | s3
    LOCAL_STORAGE_PATH: str = "./storage"
    S3_BUCKET_NAME: str = ""
    S3_REGION: str = "ap-south-1"
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""

    # --- Celery / Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # --- AI / ML ---
    OCR_LANGUAGE: str = "en"
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    ML_MODEL_DIR: str = "./ml_models"
    SIMILARITY_WEIGHT: float = 0.6
    KEYWORD_WEIGHT: float = 0.4
    AUTO_APPROVE_CONFIDENCE_THRESHOLD: float = 0.85

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 120

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
