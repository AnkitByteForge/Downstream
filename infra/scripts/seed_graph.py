"""Milestone 0 — seed the Graph Layer with the project's engineering-side
key-index (blueprint §9's Milestone 0 "done when": "a seed script can
populate one project's key-index").

Scope, deliberately narrow per explicit instruction for this milestone:
  - Reads the ACTUAL current state of the real, already-seeded Reference
    Engineering System over its REST API (never hardcodes assumed field
    values) and mirrors exactly that into Neo4j.
  - Stops at the engineering-to-commercial join boundary. docs/03 §5 and the
    Downstream Intelligence Specification §5 describe a second hop
    (SpecSection -PROCURED_UNDER-> CostCode -LINE_ITEM_OF-> PO) bridging into
    commercial artifacts. RES's real seeded RFI-214 record has cost_code =
    None (the field exists on the RFI entity but is not populated in the
    canonical seed) — so there is no real cost-code value to build a
    CostCode node from, and none is fabricated. No PO/Vendor/CostCode nodes
    are created anywhere in this script. This is a RECORDED CONTRADICTION,
    not a silent resolution: the illustrative Reference Trace's graph (docs/05
    Phase 4.1) shows a Cost Code 23-100 node the real seeded data does not
    actually support.
  - The Reference Commercial System is being implemented as a separate,
    independent system and is not depended on here, per explicit instruction.
    When it exists, its real identities attach at the SpecSection boundary
    this script already stops at — no graph-contract change required.

Nodes created: RFI, SpecSection, DrawingVersion, Location, Discipline.
Edges created: RFI-[:REFERENCES]->SpecSection, RFI-[:REFERENCES]->DrawingVersion,
RFI-[:LOCATED_AT]->Location, RFI-[:IN_DISCIPLINE]->Discipline.
Idempotent: every write is a Cypher MERGE, safe to re-run.
"""

from __future__ import annotations

import os
import sys
import time

import httpx
from neo4j import GraphDatabase


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


def authenticate(base_url: str, client_id: str, client_secret: str) -> str:
    resp = httpx.post(
        f"{base_url}/oauth/token",
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def wait_for_seeded_project(base_url: str, token: str, timeout_seconds: int = 60) -> dict:
    """RES's own seeding (alembic + run_seed) is a separate, manual step
    (IMPLEMENTATION_STATUS.md's already-established procedure, not changed
    here) — wait for it rather than assuming the project exists the instant
    the backend answers /health."""
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{base_url}/rest/v1.0/projects", headers=headers, timeout=5.0)
            resp.raise_for_status()
            projects = resp.json()
            if projects:
                return projects[0]
        except httpx.HTTPError as exc:
            last_error = exc
        time.sleep(3)
    raise RuntimeError(
        f"No seeded RES project visible after {timeout_seconds}s (has "
        f"`python -m seed.run_seed` been run inside the "
        f"reference-engineering-backend container yet?): {last_error}"
    )


def fetch_rfi214(base_url: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    project = wait_for_seeded_project(base_url, token)
    project_id = project["id"]

    rfis = httpx.get(
        f"{base_url}/rest/v1.0/projects/{project_id}/rfis",
        headers=headers,
        params={"per_page": 100},
        timeout=10.0,
    )
    rfis.raise_for_status()
    rfi = next((r for r in rfis.json() if r["display_number"] == "RFI-214"), None)
    if rfi is None:
        raise RuntimeError("RFI-214 not found — is the Reference Engineering System seeded?")

    spec_sections = httpx.get(
        f"{base_url}/rest/v1.0/projects/{project_id}/spec_sections",
        headers=headers,
        params={"per_page": 100},
        timeout=10.0,
    )
    spec_sections.raise_for_status()
    spec_by_id = {s["id"]: s for s in spec_sections.json()}

    locations = httpx.get(
        f"{base_url}/rest/v1.0/projects/{project_id}/locations",
        headers=headers,
        params={"per_page": 100},
        timeout=10.0,
    )
    locations.raise_for_status()
    location_by_id = {loc["id"]: loc for loc in locations.json()}

    # .get(), not indexing: the partial-scope credential used here
    # (rfis, submittals, documents) does NOT include "spec_sections" or
    # "locations" (verified live against the real seeded RES instance —
    # docs/04's silent-incomplete-data behavior, not an error) — so a
    # referenced id can legitimately be absent from either by-id map. This
    # is a recorded, real deviation from the illustrative Reference Trace,
    # which assumes both resolve.
    spec_section = spec_by_id.get(rfi["spec_section_ids"][0]) if rfi["spec_section_ids"] else None
    location = location_by_id.get(rfi["location_ids"][0]) if rfi["location_ids"] else None

    drawing_version = None
    drawing = None
    if rfi["drawing_version_ids"]:
        version_id = rfi["drawing_version_ids"][0]
        version_resp = httpx.get(
            f"{base_url}/rest/v1.0/projects/{project_id}/documents/versions/{version_id}",
            headers=headers,
            timeout=10.0,
        )
        version_resp.raise_for_status()
        drawing_version = version_resp.json()
        drawing_resp = httpx.get(
            f"{base_url}/rest/v1.0/projects/{project_id}/documents/{drawing_version['drawing_id']}",
            headers=headers,
            timeout=10.0,
        )
        drawing_resp.raise_for_status()
        drawing = drawing_resp.json()

    return {
        "project_id": project_id,
        "rfi": rfi,
        "spec_section": spec_section,
        "location": location,
        "drawing_version": drawing_version,
        "drawing": drawing,
    }


def seed_neo4j(uri: str, user: str, password: str, data: dict) -> None:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:
            session.execute_write(_write_subgraph, data)
    finally:
        driver.close()


def _write_subgraph(tx, data: dict) -> None:
    rfi = data["rfi"]
    tx.run(
        """
        MERGE (r:RFI {res_id: $res_id})
        SET r.display_number = $display_number,
            r.project_id = $project_id,
            r.status = $status,
            r.discipline_code = $discipline_code
        """,
        res_id=rfi["id"],
        display_number=rfi["display_number"],
        project_id=str(data["project_id"]),
        status=rfi["status"],
        discipline_code=rfi.get("discipline_code"),
    )

    if data["spec_section"]:
        section = data["spec_section"]
        tx.run(
            """
            MERGE (s:SpecSection {number: $number})
            SET s.division_number = $division_number, s.title = $title
            WITH s
            MATCH (r:RFI {res_id: $rfi_id})
            MERGE (r)-[:REFERENCES]->(s)
            """,
            number=section["number"],
            division_number=section["division_number"],
            title=section["title"],
            rfi_id=rfi["id"],
        )

    if data["drawing_version"] and data["drawing"]:
        version = data["drawing_version"]
        drawing = data["drawing"]
        tx.run(
            """
            MERGE (d:DrawingVersion {sheet_number: $sheet_number, revision_label: $revision_label})
            SET d.status = $status, d.issuance_date = $issuance_date, d.discipline_code = $discipline_code
            WITH d
            MATCH (r:RFI {res_id: $rfi_id})
            MERGE (r)-[:REFERENCES]->(d)
            """,
            sheet_number=drawing["sheet_number"],
            revision_label=version["revision_label"],
            status=version["status"],
            issuance_date=str(version["issuance_date"]),
            discipline_code=version["discipline_code"],
            rfi_id=rfi["id"],
        )

    if data["location"]:
        location = data["location"]
        tx.run(
            """
            MERGE (l:Location {name: $name})
            SET l.type = $type
            WITH l
            MATCH (r:RFI {res_id: $rfi_id})
            MERGE (r)-[:LOCATED_AT]->(l)
            """,
            name=location["name"],
            type=location["type"],
            rfi_id=rfi["id"],
        )

    if rfi.get("discipline_code"):
        tx.run(
            """
            MERGE (disc:Discipline {code: $code})
            WITH disc
            MATCH (r:RFI {res_id: $rfi_id})
            MERGE (r)-[:IN_DISCIPLINE]->(disc)
            """,
            code=rfi["discipline_code"],
            rfi_id=rfi["id"],
        )


def main() -> None:
    res_base_url = os.environ.get("RES_BASE_URL", "http://reference-engineering-backend:8000")
    client_id = os.environ.get("RES_CLIENT_ID", "downstream-partial")
    client_secret = os.environ.get("RES_CLIENT_SECRET", "partial-scope-secret")
    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://graph-db:7687")
    neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "downstream-dev")

    wait_for_res(res_base_url)
    token = authenticate(res_base_url, client_id, client_secret)
    data = fetch_rfi214(res_base_url, token)

    if data["spec_section"] is None:
        print("WARNING: RFI-214 has no resolvable spec section in RES.", file=sys.stderr)

    seed_neo4j(neo4j_uri, neo4j_user, neo4j_password, data)

    print("Neo4j engineering-side key-index seeded:")
    print(f"  RFI: {data['rfi']['display_number']} (res_id={data['rfi']['id']})")
    print(f"  SpecSection: {data['spec_section']['number'] if data['spec_section'] else None}")
    if data["drawing"] and data["drawing_version"]:
        print(f"  DrawingVersion: {data['drawing']['sheet_number']} {data['drawing_version']['revision_label']}")
    print(f"  Location: {data['location']['name'] if data['location'] else None}")
    print("  No PO/Vendor/CostCode nodes created (no real Reference Commercial System yet — by design).")


if __name__ == "__main__":
    main()
