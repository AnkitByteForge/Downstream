"""Graph Layer read path (docs/03 §5) for Milestone 2's one real,
exact-match business key: SpecSection -[:PROCURED_UNDER]-> CostCode
-[:LINE_ITEM_OF]-> POLine <-[:HAS_LINE]- PurchaseOrder -[:SUPPLIED_BY]->
Vendor. Read-only — this service never writes to the graph (that's
infra/scripts/seed_graph.py and seed_graph_commercial.py's job)."""

from __future__ import annotations

from dataclasses import dataclass

from neo4j import GraphDatabase

from config.settings import settings

_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
    return _driver


@dataclass(frozen=True)
class CommercialCandidate:
    po_rcs_id: int
    po_number: str | None
    company_code: str | None
    plant: str | None
    vendor_name: str
    cost_code_native_code: str


def find_purchase_orders_for_spec_section(spec_section_number: str) -> list[CommercialCandidate]:
    """The one real, exact-string-equality match this milestone resolves.
    No fuzzy/normalized matching — the Cypher pattern is an exact property
    match on SpecSection.number, walking only the edges
    infra/scripts/seed_graph_commercial.py actually created."""
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (s:SpecSection {number: $number})-[:PROCURED_UNDER]->(c:CostCode)
                  -[:LINE_ITEM_OF]->(l:POLine)<-[:HAS_LINE]-(p:PurchaseOrder)
                  -[:SUPPLIED_BY]->(v:Vendor)
            RETURN DISTINCT p.rcs_id AS po_rcs_id, p.po_number AS po_number,
                   p.company_code AS company_code, p.plant AS plant,
                   v.name AS vendor_name, c.native_code AS cost_code_native_code
            """,
            number=spec_section_number,
        )
        return [
            CommercialCandidate(
                po_rcs_id=record["po_rcs_id"],
                po_number=record["po_number"],
                company_code=record["company_code"],
                plant=record["plant"],
                vendor_name=record["vendor_name"],
                cost_code_native_code=record["cost_code_native_code"],
            )
            for record in result
        ]
