from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocEx API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["*"]
    STORAGE_DIR: str = "./results"
    OPENAI_API_KEY: Optional[str] = None
    VLM_PROMPT: str = "default"

    class Config:
        case_sensitive = True

settings = Settings()
