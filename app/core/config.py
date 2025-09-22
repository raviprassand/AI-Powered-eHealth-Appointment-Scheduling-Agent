from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    # App
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Patient Informatics AI Assistant"
    DEFAULT_PATIENT_ID: str = "143"
    VERCEL_ENV: str = "development"

    # OpenAI
    OPENAI_API_KEY: str = ""

    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ca-central-1"

    # --- DB / API toggles ---
    USE_DB_API: bool = False
    DATABASE_API_URL: Optional[str] = None  # only required if USE_DB_API=True

    # Direct SQL mode (e.g., SQLite)
    SQL_URI: Optional[str] = None  # e.g., "sqlite:///./demo.db"

    # Legacy MySQL fields (unused if SQL_URI is set)
    DATABASE_HOST: str = ""
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = ""
    DATABASE_PASSWORD: str = ""
    DATABASE_NAME: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # ignore unexpected env keys instead of crashing
    )

    @field_validator("DATABASE_API_URL")
    @classmethod
    def _require_api_url_if_use_api(cls, v, info):
        # if USE_DB_API=True, require DATABASE_API_URL
        values = info.data  # pydantic v2: get other fields
        if values.get("USE_DB_API") and not v:
            raise ValueError("DATABASE_API_URL must be set when USE_DB_API=True")
        return v

settings = Settings()
