from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "climate_hazard"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    rate_limit: str = "10/minute"
    cache_ttl_seconds: int = 86400
    open_meteo_timeout_seconds: float = 60.0
    port: int = 8000
    min_year: int = 1940
    max_year: int = 2024
    max_year_span: int = 80

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
