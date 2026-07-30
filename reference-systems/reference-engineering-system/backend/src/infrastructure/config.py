from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RES_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://res:res@localhost:5433/reference_engineering"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8
    cors_origins: list[str] = ["http://localhost:3100"]


settings = Settings()
