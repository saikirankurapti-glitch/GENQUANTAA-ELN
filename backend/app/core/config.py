from typing import Any, Optional
from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise ELN"
    API_V1_STR: str = "/api/v1"

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "eln_db"
    GROQ_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
