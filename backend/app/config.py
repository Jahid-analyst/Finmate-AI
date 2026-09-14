"""
Centralized configuration. Reads from environment variables / .env file.
Never hard-code secrets here.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./finmate.db"
    secret_key: str = "dev-only-insecure-secret-change-me"
    access_token_expire_minutes: int = 10080  # 7 days
    algorithm: str = "HS256"

    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"

    frontend_url: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @property
    def ai_enabled(self) -> bool:
        return bool(self.llm_api_key)


settings = Settings()
