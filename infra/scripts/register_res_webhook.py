"""Milestone 0/1 setup — registers connector-procore as the target for RES's
RFI-close webhook.

Per docs/02_Downstream_Product_Design.md's onboarding narrative ("Admin/IT...
sets up the organization, connects systems"), webhook/connection registration
is a one-time ADMIN/setup-time action, not something a connector's own
runtime code performs on every boot — so this lives here, as an explicit
setup script, not inside apps/connector-procore's application code.

RES's RegisterWebhookSubscription use case (webhook_use_cases.py) is a plain
insert with no server-side dedup, so this script checks for an existing
matching subscription first — client-side idempotency for what the server
doesn't provide.

Uses the same partial-scope client_credentials RES connection as
connector-procore's own runtime does (matching the seeded
connector_configurations row in infra/scripts/seed_connector_configuration.sql).
"""

from __future__ import annotations

import os
import time

import httpx


def wait_for_res(base_url: str, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{base_url}/health", timeout=5.0)
            if resp.status_code == 200:
                return
        except httpx.HTTPError as exc:
            last_error = exc
        time.sleep(2)
    raise RuntimeError(f"Reference Engineering System not reachable after {timeout_seconds}s: {last_error}")


def wait_for_project_seeded(base_url: str, token: str, timeout_seconds: int = 60) -> int:
    """RES's own seeding (alembic + run_seed) is a separate, manual step not
    automated by this stack (per IMPLEMENTATION_STATUS.md's already-established
    procedure, deliberately not changed here) — so this waits for the seeded
    project to actually exist rather than assuming it's ready the instant the
    backend container answers /health."""
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{base_url}/rest/v1.0/projects", headers=headers, timeout=5.0)
            resp.raise_for_status()
            projects = resp.json()
            if projects:
                return projects[0]["id"]
        except httpx.HTTPError as exc:
            last_error = exc
        time.sleep(3)
    raise RuntimeError(
        f"No seeded RES project visible after {timeout_seconds}s (has `python -m seed.run_seed` "
        f"been run inside the reference-engineering-backend container yet?): {last_error}"
    )


def main() -> None:
    res_base_url = os.environ.get("RES_BASE_URL", "http://reference-engineering-backend:8000")
    client_id = os.environ.get("RES_CLIENT_ID", "downstream-partial")
    client_secret = os.environ.get("RES_CLIENT_SECRET", "partial-scope-secret")
    connector_base_url = os.environ.get("CONNECTOR_PROCORE_BASE_URL", "http://connector-procore:8080")
    webhook_secret = os.environ.get("RES_WEBHOOK_SECRET", "seed-webhook-secret")
    # Matches the project_id seeded into connector_configurations
    # (infra/scripts/seed_connector_configuration.sql) — Downstream's own
    # project identity, distinct from RES's internal numeric project id.
    # The URL path segment below is Downstream's project addressing scheme
    # (blueprint §7's `POST /connectors/procore/{project_id}` contract);
    # RES's own numeric project id still travels inside each webhook's
    # thin payload body and is what connector-procore actually calls RES
    # with.
    downstream_project_id = os.environ.get("DOWNSTREAM_PROJECT_ID", "proj_meridian_tower")

    wait_for_res(res_base_url)

    token_resp = httpx.post(
        f"{res_base_url}/oauth/token",
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        timeout=10.0,
    )
    token_resp.raise_for_status()
    token = token_resp.json()["access_token"]

    project_id = wait_for_project_seeded(res_base_url, token)
    target_url = f"{connector_base_url}/connectors/procore/{downstream_project_id}"

    headers = {"Authorization": f"Bearer {token}"}
    existing = httpx.get(
        f"{res_base_url}/webhook_subscriptions",
        params={"project_id": project_id},
        headers=headers,
        timeout=10.0,
    )
    existing.raise_for_status()
    already_registered = any(
        s["resource_name"] == "rfis" and s["event_type"] == "update" and s["target_url"] == target_url
        for s in existing.json()
    )
    if already_registered:
        print(f"connector-procore already registered for project {project_id} at {target_url}. Nothing to do.")
        return

    resp = httpx.post(
        f"{res_base_url}/webhook_subscriptions",
        params={"project_id": project_id},
        json={
            "resource_name": "rfis",
            "event_type": "update",
            "target_url": target_url,
            "secret": webhook_secret,
        },
        headers=headers,
        timeout=10.0,
    )
    resp.raise_for_status()
    print(f"Registered connector-procore webhook subscription: {resp.json()}")


if __name__ == "__main__":
    main()
