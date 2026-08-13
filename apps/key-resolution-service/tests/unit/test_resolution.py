"""Pure-logic unit tests for domain/resolution.py — no Postgres, no Neo4j,
no Kafka."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from domain.resolution import (
    MATCH_BASIS_COST_CODE_EXACT,
    MATCH_SCORE_EXACT,
    build_artifact_ref,
    resolve_candidates,
)
from repository.graph_repository import CommercialCandidate


def _candidate(**overrides) -> CommercialCandidate:
    defaults = dict(
        po_rcs_id=1,
        po_number="4500018823",
        company_code="1000",
        plant="P100",
        vendor_name="VendorCo Metals",
        cost_code_native_code="23-100",
    )
    defaults.update(overrides)
    return CommercialCandidate(**defaults)


def test_artifact_ref_is_deterministic_from_rcs_id():
    assert build_artifact_ref(1) == "po_1"
    assert build_artifact_ref(1) == build_artifact_ref(1)


def test_artifact_ref_differs_by_rcs_id():
    assert build_artifact_ref(1) != build_artifact_ref(2)


def test_artifact_ref_never_uses_po_number():
    """po_4488 has po_number=None in real RCS data — artifact_ref must never
    depend on it existing."""
    ref = build_artifact_ref(2)
    assert ref == "po_2"
    assert "None" not in ref


def test_resolve_candidates_empty_list_is_the_unresolved_case():
    """No fabricated candidate, no default — an empty input list of
    commercial matches (nothing found in the graph) must produce an empty
    output list, not an error and not an invented result."""
    assert resolve_candidates([]) == []


def test_resolve_candidates_carries_exact_match_basis_and_score():
    resolved = resolve_candidates([_candidate()])
    assert len(resolved) == 1
    assert resolved[0].match_basis == MATCH_BASIS_COST_CODE_EXACT == "cost_code_exact"
    assert resolved[0].match_score == MATCH_SCORE_EXACT == 1.0


def test_resolve_candidates_artifact_ref_from_po_rcs_id():
    resolved = resolve_candidates([_candidate(po_rcs_id=42)])
    assert resolved[0].artifact_ref == "po_42"
    assert resolved[0].source_identifier == "42"


def test_resolve_candidates_preserves_org_scope():
    resolved = resolve_candidates([_candidate(company_code="1000", plant="P100")])
    assert resolved[0].company_code == "1000"
    assert resolved[0].plant == "P100"


def test_resolve_candidates_handles_multiple():
    resolved = resolve_candidates([_candidate(po_rcs_id=1), _candidate(po_rcs_id=3)])
    assert [r.artifact_ref for r in resolved] == ["po_1", "po_3"]


def test_no_confidence_tier_or_severity_field_exists_on_resolved_candidate():
    """Confidence/severity isolation, verified structurally: ResolvedCandidate
    must never grow a confidence-tier or severity field in this milestone."""
    resolved = resolve_candidates([_candidate()])[0]
    field_names = set(resolved.__dataclass_fields__.keys())
    assert "confidence_tier" not in field_names
    assert "severity" not in field_names
