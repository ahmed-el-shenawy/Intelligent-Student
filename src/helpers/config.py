from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    MAX_FILE_SIZE_MB: int
    ALLOWED_MIME_TYPES: list[str]

    POSTGRES_USER: str
    POSTGRES_PASSWORD : str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    GROQ_API_KEY: str
    GROQ_BASE_URL: str
    GROQ_MODEL: str

    OLLAMA_API_KEY: str
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    SECRET_KEY: str
    ALGORITHM: str
@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
