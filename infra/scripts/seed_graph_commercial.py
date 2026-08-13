"""Milestone 2 — commercial-side graph calibration.

Reads REAL data from the running Reference Commercial System over its real
REST API, authenticated via its real OAuth2 client_credentials grant (never
hardcoded/synthetic values), and MERGEs it into the SAME Neo4j graph
Milestone 0's engineering-side seed_graph.py already populated — this
script never touches or recreates the RFI/SpecSection/DrawingVersion/
Location/Discipline nodes, only adds to the graph alongside them.

Node types created (RCS's real internal `id`, never `po_number` — po_4488's
po_number is null, per RCS's own ADR-017; a numeric internal id is the only
identifier every PurchaseOrder actually has, mirroring the same
id-vs-display-number discipline RES's own `display_number` already
established):
  CostCode, PurchaseOrder, POLine, Vendor.

Edges created:
  (SpecSection)-[:PROCURED_UNDER]->(CostCode)   -- business-key match:
      CostCode.standard_ref == SpecSection.number, gated on
      CostCode.cost_code_format == "CSI_MASTERFORMAT". Exact string
      equality only -- no fuzzy/normalized matching. Only created when a
      SpecSection node with that exact number already exists in the graph
      (from the engineering-side calibration) -- Scenario B's cost code
      ("26-200" -> "26 24 13") is real RCS data but has no matching
      SpecSection node yet (the engineering calibration never traversed
      ASI-07's affected_spec_section_ids, only RFI-214's own references),
      so no edge is created for it. This is the natural, non-special-cased
      outcome the approved plan asked for -- not a Scenario-A/B branch in
      this script's own logic.
  (CostCode)-[:LINE_ITEM_OF]->(POLine)          -- real, from POLine.cost_code_id.
      Absent wherever cost_code_id is null (po_4488's and po_4512's real
      lines, verified live) -- never invented.
  (PurchaseOrder)-[:HAS_LINE]->(POLine)          -- real, structural (RCS's
      schema splits vendor onto the PO header and cost_code/spec onto the
      line -- one hop the illustrative Reference Trace's flattened "PO"
      object doesn't show).
  (PurchaseOrder)-[:SUPPLIED_BY]->(Vendor)       -- real, from PurchaseOrder.vendor_id.

RECORDED, LIVE-VERIFIED API LIMITATION (not a design guess): RCS's
`GET /rest/v1/purchase_orders/{po_number}/lines` is keyed by `po_number`,
which is nullable and IS null on po_4488 (docs/05: "not stated in trace";
ADR-017). There is no internal-id-keyed lines endpoint. po_4488's POLine is
therefore structurally unreachable through RCS's real, current API -- not
merely unresolved by a missing cost code. This script still creates
po_4488's own PurchaseOrder node (real data, from the list endpoint, which
does carry its internal id and vendor_id) and its SUPPLIED_BY edge, but
cannot create its POLine node or HAS_LINE edge. Recorded in the Milestone 2
report's "unresolved real data cases" section, not silently worked around.

Scope: Scenario A only, by construction, not by a special case. The RCS
credential used (`downstream-full-scope`, company_code "1000") is real-scope-
bound per ADR-012's org-scope isolation -- RCS's own `list_purchase_orders`
route filters an integration client's results to its own company_code even
under "full" resource-type scope. Scenario B's POs (company_code "2000")
are therefore invisible to this credential and this script by construction,
not by a conditional this script writes.
"""

from __future__ import annotations

import os
import sys
import time

import httpx
from neo4j import GraphDatabase


def wait_for_rcs(base_url: str, timeout_seconds: int = 60) -> None:
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
    raise RuntimeError(f"Reference Commercial System not reachable after {timeout_seconds}s: {last_error}")


def authenticate(base_url: str, client_id: str, client_secret: str) -> str:
    resp = httpx.post(
        f"{base_url}/oauth/token",
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_commercial_data(base_url: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}

    cost_codes = httpx.get(
        f"{base_url}/rest/v1/cost_codes", headers=headers, params={"per_page": 100}, timeout=10.0
    )
    cost_codes.raise_for_status()
    cost_codes = cost_codes.json()

    purchase_orders = httpx.get(
        f"{base_url}/rest/v1/purchase_orders", headers=headers, params={"per_page": 100}, timeout=10.0
    )
    purchase_orders.raise_for_status()
    purchase_orders = purchase_orders.json()

    vendors = httpx.get(f"{base_url}/rest/v1/vendors", headers=headers, params={"per_page": 100}, timeout=10.0)
    vendors.raise_for_status()
    vendor_by_id = {v["id"]: v for v in vendors.json()}

    pos_with_lines: list[tuple[dict, list[dict]]] = []
    for po in purchase_orders:
        if po["po_number"]:
            lines_resp = httpx.get(
                f"{base_url}/rest/v1/purchase_orders/{po['po_number']}/lines", headers=headers, timeout=10.0
            )
            lines_resp.raise_for_status()
            lines = lines_resp.json()
        else:
            # Live-verified limitation (module docstring): no internal-id-
            # keyed lines endpoint exists, so a PO with no po_number has no
            # fetchable lines at all through RCS's real API.
            lines = []
        pos_with_lines.append((po, lines))

    return {"cost_codes": cost_codes, "pos_with_lines": pos_with_lines, "vendor_by_id": vendor_by_id}


def seed_neo4j(uri: str, user: str, password: str, data: dict) -> dict:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:
            return session.execute_write(_write_commercial_subgraph, data)
    finally:
        driver.close()


def _write_commercial_subgraph(tx, data: dict) -> dict:
    summary = {"cost_codes": 0, "procured_under_edges": 0, "purchase_orders": 0, "po_lines": 0, "vendors": 0}

    # CostCode nodes + the one business-key edge this milestone resolves.
    for cc in data["cost_codes"]:
        tx.run(
            """
            MERGE (c:CostCode {rcs_id: $rcs_id})
            SET c.native_code = $native_code,
                c.cost_code_format = $cost_code_format,
                c.standard_ref = $standard_ref,
                c.company_code = $company_code,
                c.plant = $plant
            """,
            rcs_id=cc["id"],
            native_code=cc["native_code"],
            cost_code_format=cc["cost_code_format"],
            standard_ref=cc["standard_ref"],
            company_code=cc["org_scope"].get("company_code"),
            plant=cc["org_scope"].get("plant"),
        )
        summary["cost_codes"] += 1

        if cc["cost_code_format"] != "CSI_MASTERFORMAT" or not cc["standard_ref"]:
            continue

        # Exact string-equality business-key match only -- no fuzzy/
        # normalized matching. MATCH (not MERGE) on SpecSection: this
        # script never creates engineering-side nodes, only reads them.
        result = tx.run(
            """
            MATCH (s:SpecSection {number: $number})
            MATCH (c:CostCode {rcs_id: $rcs_id})
            MERGE (s)-[r:PROCURED_UNDER]->(c)
            SET r.match_basis = 'cost_code_exact', r.matched_at = datetime()
            RETURN count(r) AS n
            """,
            number=cc["standard_ref"],
            rcs_id=cc["id"],
        ).single()
        summary["procured_under_edges"] += result["n"]

    # PurchaseOrder + POLine + Vendor nodes and their real, structural edges.
    for po, lines in data["pos_with_lines"]:
        tx.run(
            """
            MERGE (p:PurchaseOrder {rcs_id: $rcs_id})
            SET p.po_number = $po_number, p.currency = $currency, p.status = $status,
                p.company_code = $company_code, p.plant = $plant
            """,
            rcs_id=po["id"],
            po_number=po["po_number"],
            currency=po["currency"],
            status=po["status"],
            company_code=po["org_scope"].get("company_code"),
            plant=po["org_scope"].get("plant"),
        )
        summary["purchase_orders"] += 1

        vendor = data["vendor_by_id"].get(po["vendor_id"])
        if vendor is not None:
            tx.run(
                """
                MERGE (v:Vendor {rcs_id: $rcs_id})
                SET v.name = $name, v.qualification_status = $qualification_status
                WITH v
                MATCH (p:PurchaseOrder {rcs_id: $po_rcs_id})
                MERGE (p)-[:SUPPLIED_BY]->(v)
                """,
                rcs_id=vendor["id"],
                name=vendor["name"],
                qualification_status=vendor["qualification_status"],
                po_rcs_id=po["id"],
            )
            summary["vendors"] += 1

        for line in lines:
            tx.run(
                """
                MERGE (l:POLine {rcs_id: $rcs_id})
                SET l.line_no = $line_no, l.description = $description,
                    l.value = $value, l.lifecycle_position = $lifecycle_position
                WITH l
                MATCH (p:PurchaseOrder {rcs_id: $po_rcs_id})
                MERGE (p)-[:HAS_LINE]->(l)
                """,
                rcs_id=line["id"],
                line_no=line["line_no"],
                description=line["description"],
                value=line["value"],
                lifecycle_position=line["lifecycle_position"],
                po_rcs_id=po["id"],
            )
            summary["po_lines"] += 1

            if line["cost_code_id"] is not None:
                tx.run(
                    """
                    MATCH (c:CostCode {rcs_id: $cost_code_id})
                    MATCH (l:POLine {rcs_id: $line_rcs_id})
                    MERGE (c)-[:LINE_ITEM_OF]->(l)
                    """,
                    cost_code_id=line["cost_code_id"],
                    line_rcs_id=line["id"],
                )

    return summary


def main() -> None:
    rcs_base_url = os.environ.get("RCS_BASE_URL", "http://reference-commercial-backend:8000")
    client_id = os.environ.get("RCS_CLIENT_ID", "downstream-full-scope")
    client_secret = os.environ.get("RCS_CLIENT_SECRET", "demo-client-secret")
    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://graph-db:7687")
    neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "downstream-dev")

    wait_for_rcs(rcs_base_url)
    token = authenticate(rcs_base_url, client_id, client_secret)
    data = fetch_commercial_data(rcs_base_url, token)
    summary = seed_neo4j(neo4j_uri, neo4j_user, neo4j_password, data)

    print("Neo4j commercial-side graph calibrated:")
    print(f"  CostCode nodes: {summary['cost_codes']}")
    print(f"  PROCURED_UNDER edges (real SpecSection<->CostCode business-key matches): {summary['procured_under_edges']}")
    print(f"  PurchaseOrder nodes: {summary['purchase_orders']}")
    print(f"  POLine nodes: {summary['po_lines']}")
    print(f"  Vendor nodes: {summary['vendors']}")
    if summary["procured_under_edges"] == 0:
        print(
            "  WARNING: zero PROCURED_UNDER edges created — run the engineering-side "
            "seed_graph.py first (RFI-214's SpecSection must already be in the graph).",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
