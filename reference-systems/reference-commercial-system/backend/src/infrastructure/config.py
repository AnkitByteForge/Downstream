from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CS_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://cs:cs@localhost:5434/reference_commercial"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8

    # OAuth2 client_credentials access tokens (docs/04: SAP/Oracle-shaped
    # integration is service-account, not user-delegated — no refresh grant).
    oauth_access_token_expire_minutes: int = 60

    # CSRF ceremony (docs/04, docs/05 Phase 12.2): a token issued on a GET
    # carrying "X-CSRF-Token: fetch" must be echoed on the following write.
    csrf_token_expire_minutes: int = 15

    cors_origins: list[str] = ["http://localhost:3200"]


settings = Settings()
