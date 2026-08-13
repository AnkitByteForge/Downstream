"""Pure resolution logic — no I/O, fully unit-testable.

Confidence handling, explicitly isolated (per the approved Milestone 2
plan's own §J): this module computes ONLY `match_score`/`match_basis` —
packages/event-contracts/keys_resolved.py's already-frozen, unmodified
shape. It never computes a confidence tier (CERTAIN/PROBABLE/POSSIBLE —
Reasoning Pipeline stage 6c) and never computes a severity number (stage
6d). The unresolved confidence-vs-severity independence conflict flagged in
the Milestone 1 report has no surface area here."""

from __future__ import annotations

from dataclasses import dataclass

from repository.graph_repository import CommercialCandidate

MATCH_BASIS_COST_CODE_EXACT = "cost_code_exact"
MATCH_SCORE_EXACT = 1.0


@dataclass(frozen=True)
class ResolvedCandidate:
    artifact_ref: str
    match_basis: str
    match_score: float
    source_identifier: str
    company_code: str | None
    plant: str | None


def build_artifact_ref(rcs_po_id: int) -> str:
    """Deterministic — derived from RCS's real internal PurchaseOrder id,
    never from po_number (nullable, cosmetic — po_4488 has none, mirroring
    RES's own id-vs-display_number discipline) and never a random
    generate_id() suffix. This is what makes re-resolution idempotent:
    resolving the same real PO twice always yields the same artifact_ref."""
    return f"po_{rcs_po_id}"


def resolve_candidates(commercial_candidates: list[CommercialCandidate]) -> list[ResolvedCandidate]:
    """Every candidate reaching this function already passed the one real,
    exact-match business key (SpecSection.number == CostCode.standard_ref,
    CostCode.cost_code_format == CSI_MASTERFORMAT) at the graph-query layer
    (graph_repository.find_purchase_orders_for_spec_section) — so every
    candidate here is, today, exactly the same match_basis/match_score.
    No fuzzy matching, no free-text matching, no vendor-name matching, no
    inferred PO relationship — an empty list is a legitimate, honest
    result (docs/03: an INSUFFICIENT/no-match case is preserved, never
    silently filled)."""
    return [
        ResolvedCandidate(
            artifact_ref=build_artifact_ref(c.po_rcs_id),
            match_basis=MATCH_BASIS_COST_CODE_EXACT,
            match_score=MATCH_SCORE_EXACT,
            source_identifier=str(c.po_rcs_id),
            company_code=c.company_code,
            plant=c.plant,
        )
        for c in commercial_candidates
    ]
