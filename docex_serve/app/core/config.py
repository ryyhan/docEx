from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocEx API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["*"]
    STORAGE_DIR: str = "./results"
    
    # VLM API Configuration
    VLM_API_PROVIDER: str = "openai"  # Options: openai, groq, anthropic, google, azure, custom
    VLM_API_KEY: Optional[str] = None  # API key for the selected provider
    VLM_API_BASE_URL: Optional[str] = None  # Custom endpoint URL (for azure or custom providers)
    
    # Legacy support (deprecated, use VLM_API_KEY instead)
    OPENAI_API_KEY: Optional[str] = None
    
    VLM_PROMPT: str = "default"

    class Config:
        case_sensitive = True
        env_file = ".env"  # Load from .env file
        env_file_encoding = "utf-8"

settings = Settings()
