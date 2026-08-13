"""Inbound webhook receiver — blueprint §7's contract:
`POST /connectors/procore/{project_id}` -> `202 Accepted`.

{project_id} in the URL path is Downstream's own project_id (e.g.
"proj_meridian_tower"), matching blueprint §7's addressing scheme — distinct
from RES's own internal numeric project id, which travels inside the thin
webhook payload body itself (RES infrastructure/webhooks/dispatcher.py /
application/webhook_payloads.py build_thin_payload's own `project_id` field)
and is what this receiver actually calls RES with.

Processing happens synchronously within the request (idempotency check ->
RES enrichment GET-back -> reference resolution -> envelope construction ->
handoff to ingestion-service) rather than via a background queue: no frozen
document calls for an async worker here, RES's own webhook dispatch timeout
(5s, infrastructure/config.py webhook_timeout_seconds) comfortably covers
this milestone's one-RFI chain, and 202 is still the honest response code —
"accepted", not a promise the caller must wait synchronously for.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging

from fastapi import FastAPI, HTTPException, Request, Response, status

from client.ingestion_client import submit_envelope
from client.res_client import ResClient
from idempotency.cache import already_seen, build_cache_key, mark_seen
from mapper.rfi_mapper import map_rfi_to_envelope
from repository.connector_configuration_repository import get_configuration

from config.settings import settings

logger = logging.getLogger("connector-procore")

app = FastAPI(title="Downstream — connector-procore")

_config = None
_res_client: ResClient | None = None


def _get_config():
    global _config, _res_client
    if _config is None:
        _config = get_configuration(settings.connection_id)
        _res_client = ResClient(_config)
    return _config, _res_client


def _verify_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/connectors/procore/{project_id}", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(project_id: str, request: Request, response: Response) -> dict:
    config, res_client = _get_config()
    if project_id != config.project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown project_id: {project_id!r}")

    raw_body = await request.body()
    signature = request.headers.get("X-Signature")
    if not _verify_signature(config.webhook_secret, raw_body, signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing webhook signature")

    payload = json.loads(raw_body)
    resource_name = payload["resource_name"]
    resource_id = payload["resource_id"]
    res_project_id = payload["project_id"]
    event_type = payload["event_type"]
    timestamp = payload["timestamp"]

    cache_key = build_cache_key(resource_name, resource_id, event_type, timestamp)

    # Phase 1.1 of the Reference Execution Trace: redelivery of an
    # already-seen webhook stops here, before any RES call or downstream
    # handoff — the idempotency guarantee docs/03/05 both name as the
    # system's "first and most important defense".
    if already_seen(cache_key):
        logger.info("Redelivery detected, cache_key=%s — no further processing.", cache_key)
        return {"outcome": "duplicate_ignored", "cache_key": cache_key}

    if resource_name != "rfis" or event_type != "update":
        logger.info("Ignoring non-RFI-close event: %s/%s", resource_name, event_type)
        # Marked seen here (not up front): a non-RFI-close event is fully
        # handled with nothing left to retry, so recording it now is safe.
        mark_seen(cache_key)
        return {"outcome": "ignored_resource_type"}

    # Marked seen only once the full chain below actually succeeds — not
    # before RES's GET-back / ingestion handoff — so a genuine transient
    # failure (a network blip, ingestion-service momentarily down) leaves
    # the cache key unmarked and a legitimate RES redelivery can still be
    # processed, rather than being silently swallowed as a "duplicate" of
    # an attempt that never actually completed (docs/03: a failure must
    # surface, never disappear silently).
    rfi = res_client.get_rfi(res_project_id, resource_id)
    resolved = res_client.resolve_rfi_references(res_project_id, rfi)
    envelope = map_rfi_to_envelope(resolved, config)

    result = submit_envelope(settings.ingestion_service_url, config.project_id, envelope)
    mark_seen(cache_key)
    logger.info(
        "Envelope submitted for RFI %s: outcome=%s trigger_id=%s",
        rfi["display_number"],
        result.outcome,
        result.trigger_id,
    )
    return {"outcome": result.outcome, "trigger_id": result.trigger_id, "source_id": envelope.source_id}
