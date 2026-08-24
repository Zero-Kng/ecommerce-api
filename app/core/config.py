from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da aplicação, lida de variáveis de ambiente ou do arquivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    project_name: str = "E-commerce API"
    database_url: str


@lru_cache
def get_settings() -> Settings:
    """Devolve a configuração, lendo o ambiente apenas na primeira chamada."""
    return Settings()
