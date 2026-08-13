"""connector-procore runtime configuration.

Only what this milestone actually needs: where to reach the Operational DB
(for its own idempotency cache and the connector configuration store) and
where to reach ingestion-service for the synchronous handoff (blueprint §1's
diagram: a direct arrow, not an event-bus hop). Per-connection RES
credentials/base URL live in the connector_configurations table, not here —
this file has no RES-specific fields, since a real connector could have many
connection rows.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CONNECTOR_PROCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres@localhost:5432/downstream_operational"
    ingestion_service_url: str = "http://localhost:8100"
    host: str = "0.0.0.0"
    port: int = 8080

    # Which connector_configurations row this instance acts as. Milestone 1
    # has exactly one connection (RES/Meridian Tower); a real multi-project
    # deployment would look this up per inbound project_id instead.
    connection_id: str = "conn_res_meridian"


settings = Settings()
