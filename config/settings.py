from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """
    Central configuration for NanoClaw.
    All environment variables are loaded here.
    """
    # Telegram
    telegram_token: str

    # Terminal
    
    
    # Gateway
    secret_key: str
    
    # LLM
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "llama3.1"
    
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # Agent
    max_history: int = 10
    request_timeout: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loads once, reused everywhere."""
    return Settings()