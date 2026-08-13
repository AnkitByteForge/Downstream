from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INGESTION_", env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres@localhost:5432/downstream_operational"
    kafka_bootstrap_servers: str = "localhost:9092"
    host: str = "0.0.0.0"
    port: int = 8100


settings = Settings()
