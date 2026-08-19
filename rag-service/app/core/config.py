import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
_ENV_FILE = os.path.join(_BASE_DIR, ".env")


class Settings(BaseSettings):
    SUPABASE_URL: str = "http://localhost:54321"
    SUPABASE_SERVICE_ROLE_KEY: str = "placeholder_key"
    OPENROUTER_API_KEY: str = "placeholder_key"
    OPENROUTER_MODEL: str = "openrouter/free"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K: int = 5
    RAG_INTERNAL_SECRET: str = "dev_internal_secret_change_in_prod"

    # Optional CORS Allowed Origins (comma-separated string or list)
    ALLOWED_ORIGINS: str = ""

    # Ingestion Batching & Retry Configuration
    INGESTION_BATCH_SIZE: int = 25
    INGESTION_MAX_RETRIES: int = 3
    INGESTION_RETRY_DELAY: float = 1.0

    @property
    def cors_origins(self) -> List[str]:
        default_origins = [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
        if self.ALLOWED_ORIGINS:
            custom_origins = [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
            return list(set(default_origins + custom_origins))
        return default_origins

    model_config = SettingsConfigDict(
        env_file=(_ENV_FILE, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
