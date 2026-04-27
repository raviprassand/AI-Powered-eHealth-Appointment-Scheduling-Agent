from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    # ---------------------------------------------------------
    # App
    # ---------------------------------------------------------
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Patient Informatics AI Assistant"
    DEFAULT_PATIENT_ID: str = "143"
    VERCEL_ENV: str = "development"

    # ---------------------------------------------------------
    # OpenAI / LLM / RAG
    # ---------------------------------------------------------
    OPENAI_API_KEY: str = ""

    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    USE_LLM_INTENT: bool = True
    USE_RAG: bool = True
    USE_VECTOR_SEARCH: bool = False

    OPENAI_TTS_MODEL: str = "tts-1"
    OPENAI_TTS_VOICE: str = "alloy"

    # ---------------------------------------------------------
    # AWS
    # ---------------------------------------------------------
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ca-central-1"

    # ---------------------------------------------------------
    # DB / API toggles
    # ---------------------------------------------------------
    USE_DB_API: bool = False
    DATABASE_API_URL: Optional[str] = None

    SQL_URI: Optional[str] = None

    DATABASE_HOST: str = ""
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = ""
    DATABASE_PASSWORD: str = ""
    DATABASE_NAME: str = ""

    # ---------------------------------------------------------
    # RAG settings
    # ---------------------------------------------------------
    RAG_TOP_K: int = 5
    VECTOR_SIMILARITY_THRESHOLD: float = 0.25

    # ---------------------------------------------------------
    # Appointment settings
    # ---------------------------------------------------------
    DEFAULT_APPOINTMENT_HOUR: int = 9
    APPOINTMENT_CONFLICT_WINDOW_MINUTES: int = 30

    # ---------------------------------------------------------
    # Runtime behavior
    # ---------------------------------------------------------
    DEBUG_RAG: bool = False
    DEBUG_LLM: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("DATABASE_API_URL")
    @classmethod
    def _require_api_url_if_use_api(cls, v, info):
        values = info.data
        if values.get("USE_DB_API") and not v:
            raise ValueError("DATABASE_API_URL must be set when USE_DB_API=True")
        return v

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def _warn_if_llm_enabled_without_key(cls, v, info):
        values = info.data
        use_llm = values.get("USE_LLM_INTENT", True)
        use_rag = values.get("USE_RAG", True)
        use_vector = values.get("USE_VECTOR_SEARCH", False)

        if (use_llm or use_rag or use_vector) and not v:
            # Do not crash app; services will use deterministic fallback.
            return ""
        return v


settings = Settings()