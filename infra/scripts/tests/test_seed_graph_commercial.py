"""Pure-logic unit test for the one CSI-format-validation gate
seed_graph_commercial.py applies before ever attempting the
SpecSection<->CostCode business-key match — no Neo4j, no RCS, no network."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seed_graph_commercial import is_csi_masterformat_with_standard_ref


def test_csi_masterformat_with_standard_ref_is_eligible():
    cost_code = {"cost_code_format": "CSI_MASTERFORMAT", "standard_ref": "23 31 13"}
    assert is_csi_masterformat_with_standard_ref(cost_code) is True


def test_non_csi_format_is_not_eligible():
    """A SAP_WBS or Oracle Project/Task cost code must never be string-matched
    against a CSI MasterFormat SpecSection.number — docs/04's whole point in
    adding cost_code_format in the first place."""
    cost_code = {"cost_code_format": "SAP_WBS", "standard_ref": "23 31 13"}
    assert is_csi_masterformat_with_standard_ref(cost_code) is False


def test_csi_masterformat_with_no_standard_ref_is_not_eligible():
    cost_code = {"cost_code_format": "CSI_MASTERFORMAT", "standard_ref": None}
    assert is_csi_masterformat_with_standard_ref(cost_code) is False


def test_csi_masterformat_with_empty_string_standard_ref_is_not_eligible():
    cost_code = {"cost_code_format": "CSI_MASTERFORMAT", "standard_ref": ""}
    assert is_csi_masterformat_with_standard_ref(cost_code) is False
