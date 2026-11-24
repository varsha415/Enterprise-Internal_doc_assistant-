from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Paths
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chroma_db")
    DOCUMENTS_DIR: str = str(BASE_DIR / "data" / "documents")
    SQLITE_DB_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'acme_enterprise.db'}"

    # LLM & Embeddings
    EMBEDDING_PROVIDER: Literal["chroma", "openai", "mock"] = "chroma"
    LLM_PROVIDER: Literal["mock", "openai"] = "mock"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Auth
    JWT_SECRET_KEY: str = "acme-tech-insecure-dev-secret-change-in-production-2026!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Rate Limiting
    RATE_LIMIT_ASK: str = "30/minute"

    # Standard exact not found response
    EXACT_NOT_FOUND_REPLY: str = "I couldn't find that in the documents available to you."

settings = Settings()
