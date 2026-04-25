from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://archaeologist:archaeologist_secret@localhost:5432/archaeologist_db"
    database_url_sync: str = "postgresql://archaeologist:archaeologist_secret@localhost:5432/archaeologist_db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "dev_secret_key_change_in_production"
    repos_dir: str = "./repos"
    debug: bool = True

    github_token: str = ""

    llm_provider: str = "anthropic"  # openai | anthropic | none
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    embedding_provider: str = "anthropic"  # openai | anthropic | none
    embedding_model: str = "voyage-code-2"

    cors_origins: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def repos_path(self) -> str:
        path = self.repos_dir
        os.makedirs(path, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
