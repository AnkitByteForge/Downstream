"""key-resolution-service runtime configuration.

Reads Triggers directly from operational-db (Step 6 of the approved
Milestone 2 implementation instructions: "It reads the corresponding
Trigger from the operational DB") — a read-only cross-service query against
ingestion-service's own `triggers` table. Recorded explicitly: blueprint
§6's general storage rule prefers "from an event, never a cross-service
query," but `trigger.detected` (packages/event-contracts/trigger_detected.py)
carries only {trigger_id, project_id, occurred_at} — no reference lists —
so a follow-up fetch is unavoidable either way; the approved instruction
settles it as a direct, read-only DB query rather than a new synchronous
API endpoint on ingestion-service."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KEY_RESOLUTION_", env_file=".env", extra="ignore")

    operational_database_url: str = "postgresql://postgres@localhost:5432/downstream_operational"
    kafka_bootstrap_servers: str = "localhost:9092"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "downstream-dev"
    consumer_group_id: str = "key-resolution-service"


settings = Settings()
