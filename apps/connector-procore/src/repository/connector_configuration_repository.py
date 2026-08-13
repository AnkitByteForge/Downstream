"""Reads this connector's own connection configuration (RES base URL, OAuth
client credentials, granted scope, webhook secret) from the
connector_configurations table (infra/migrations/0001_connector_configuration.sql
— owned at the Connector Layer level, per docs/07 §6's "shared across
adapters" treatment)."""

from __future__ import annotations

from dataclasses import dataclass

from repository.db import get_connection


@dataclass(frozen=True)
class ConnectorConfiguration:
    connection_id: str
    project_id: str
    source_system: str
    base_url: str
    oauth_token_url: str
    oauth_client_id: str
    oauth_client_secret: str
    granted_scope: list[str]
    integration_tier: str
    webhook_secret: str


def get_configuration(connection_id: str) -> ConnectorConfiguration:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT connection_id, project_id, source_system, base_url, oauth_token_url,
                   oauth_client_id, oauth_client_secret, granted_scope, integration_tier,
                   webhook_secret
            FROM connector_configurations
            WHERE connection_id = %s
            """,
            (connection_id,),
        ).fetchone()
    if row is None:
        raise LookupError(f"No connector_configurations row for connection_id={connection_id!r}")
    return ConnectorConfiguration(
        connection_id=row[0],
        project_id=row[1],
        source_system=row[2],
        base_url=row[3],
        oauth_token_url=row[4],
        oauth_client_id=row[5],
        oauth_client_secret=row[6],
        granted_scope=list(row[7]),
        integration_tier=row[8],
        webhook_secret=row[9],
    )
