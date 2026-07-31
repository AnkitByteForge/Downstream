from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RES_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://res:res@localhost:5433/reference_engineering"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8
    cors_origins: list[str] = ["http://localhost:3100"]

    # Rate limiting (docs/04: a configurable per-client_id request budget —
    # Procore's real ceiling is 3,600/hour; kept configurable, not hardcoded,
    # so contract tests can exercise the 429 path with a small window/budget.
    rate_limit_window_seconds: int = 3600
    rate_limit_max_requests: int = 3600

    webhook_timeout_seconds: float = 5.0


settings = Settings()
