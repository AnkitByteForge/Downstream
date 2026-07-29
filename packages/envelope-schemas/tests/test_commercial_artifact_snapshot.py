from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from envelope_schemas import CommercialArtifactSnapshot, OrgScope


def _base_kwargs(**overrides):
    kwargs = dict(
        source_system="sap",
        source_id="4500018823",
        artifact_type="PO",
        cost_code="23-100",
        cost_code_format="SAP_WBS",
        spec_section_refs=["23 31 13"],
        lifecycle_position="IN_FABRICATION",
        value=820000.0,
        vendor_ref="vendorco-metals",
        project_ref="proj_8841",
        org_scope=OrgScope(company_code="1000", plant="P100"),
        data_freshness_path="polled",
        fetched_at=datetime(2026, 7, 28, 9, 14, 5, tzinfo=timezone.utc),
    )
    kwargs.update(overrides)
    return kwargs


class TestCommercialArtifactSnapshotHappyPath:
    def test_reference_trace_po_4471_shape(self):
        snapshot = CommercialArtifactSnapshot(**_base_kwargs())

        assert snapshot.envelope_type == "CommercialArtifactSnapshot"
        assert snapshot.source_system == "sap"
        assert snapshot.source_id == "4500018823"
        assert snapshot.artifact_type == "PO"
        assert snapshot.lifecycle_position == "IN_FABRICATION"
        assert snapshot.value == 820000.0
        assert snapshot.project_ref == "proj_8841"
        assert snapshot.org_scope.company_code == "1000"
        assert snapshot.org_scope.plant == "P100"
        assert snapshot.data_freshness_path == "polled"

    def test_serializes_to_json_and_back(self):
        snapshot = CommercialArtifactSnapshot(**_base_kwargs())
        restored = CommercialArtifactSnapshot.model_validate_json(snapshot.model_dump_json())
        assert restored == snapshot

    @pytest.mark.parametrize("artifact_type", ["PO", "VENDOR", "DELIVERY"])
    def test_accepts_all_three_artifact_types(self, artifact_type):
        snapshot = CommercialArtifactSnapshot(**_base_kwargs(artifact_type=artifact_type))
        assert snapshot.artifact_type == artifact_type

    @pytest.mark.parametrize(
        "fmt",
        [
            "CSI_MASTERFORMAT",
            "SAP_WBS",
            "ORACLE_PROJECT_TASK",
            "ERPNEXT_COST_CENTER",
            "CUSTOMER_DEFINED",
        ],
    )
    def test_accepts_all_five_cost_code_formats(self, fmt):
        snapshot = CommercialArtifactSnapshot(**_base_kwargs(cost_code_format=fmt))
        assert snapshot.cost_code_format == fmt

    @pytest.mark.parametrize("path", ["real_time_event", "polled", "bulk_import"])
    def test_accepts_all_three_data_freshness_paths(self, path):
        snapshot = CommercialArtifactSnapshot(**_base_kwargs(data_freshness_path=path))
        assert snapshot.data_freshness_path == path

    def test_only_project_ref_and_identity_fields_are_required(self):
        snapshot = CommercialArtifactSnapshot(
            source_system="sap",
            source_id="4500018823",
            artifact_type="PO",
            project_ref="proj_8841",
        )
        assert snapshot.cost_code is None
        assert snapshot.cost_code_format is None
        assert snapshot.spec_section_refs == []
        assert snapshot.lifecycle_position is None
        assert snapshot.value is None
        assert snapshot.vendor_ref is None
        assert snapshot.org_scope is None
        assert snapshot.data_freshness_path is None
        assert snapshot.fetched_at is None


class TestCommercialArtifactSnapshotValidation:
    def test_rejects_invalid_artifact_type(self):
        with pytest.raises(ValidationError):
            CommercialArtifactSnapshot(**_base_kwargs(artifact_type="INVOICE"))

    def test_rejects_invalid_cost_code_format(self):
        with pytest.raises(ValidationError):
            CommercialArtifactSnapshot(**_base_kwargs(cost_code_format="MADE_UP_FORMAT"))

    def test_rejects_invalid_data_freshness_path(self):
        with pytest.raises(ValidationError):
            CommercialArtifactSnapshot(**_base_kwargs(data_freshness_path="telepathy"))

    def test_rejects_missing_project_ref(self):
        kwargs = _base_kwargs()
        del kwargs["project_ref"]
        with pytest.raises(ValidationError):
            CommercialArtifactSnapshot(**kwargs)

    def test_rejects_empty_project_ref(self):
        with pytest.raises(ValidationError):
            CommercialArtifactSnapshot(**_base_kwargs(project_ref=""))

    def test_is_frozen(self):
        snapshot = CommercialArtifactSnapshot(**_base_kwargs())
        with pytest.raises(ValidationError):
            snapshot.value = 1.0


class TestOrgScope:
    def test_all_fields_optional(self):
        scope = OrgScope()
        assert scope.company_code is None
        assert scope.plant is None
        assert scope.business_unit is None

    def test_generalizes_sap_dimensions(self):
        scope = OrgScope(company_code="1000", plant="P100")
        assert scope.company_code == "1000"
        assert scope.plant == "P100"
        assert scope.business_unit is None

    def test_generalizes_oracle_dimension(self):
        scope = OrgScope(business_unit="BU_CONSTRUCTION")
        assert scope.business_unit == "BU_CONSTRUCTION"

    def test_is_frozen(self):
        scope = OrgScope(company_code="1000")
        with pytest.raises(ValidationError):
            scope.company_code = "2000"
