from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # =========================================================
    # APPLICATION
    # =========================================================

    APP_NAME: str = "NEXUS"
    DEBUG: bool = False


    # =========================================================
    # DATABASE
    # =========================================================

    DATABASE_URL: str = (
        "postgresql://nexus:nexus@localhost:5432/nexus"
    )


    # =========================================================
    # NEO4J
    # =========================================================

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "nexus-nexus"


    # =========================================================
    # QDRANT
    # =========================================================

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "nexus_content"


    # =========================================================
    # REDIS
    # =========================================================

    REDIS_URL: str = "redis://localhost:6379"


    # =========================================================
    # SECURITY
    # =========================================================

    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


    # =========================================================
    # OPENAI
    # =========================================================

    OPENAI_API_KEY: str = ""

    # Used for narrative extraction.
    # If unavailable, the NarrativeDNAAgent must use
    # its local fallback extraction.
    OPENAI_MODEL: str = "gpt-5.6-luna"


    # =========================================================
    # STORAGE
    # =========================================================

    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024


    # =========================================================
    # PYDANTIC SETTINGS
    # =========================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# =============================================================
# SETTINGS SINGLETON
# =============================================================

@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()