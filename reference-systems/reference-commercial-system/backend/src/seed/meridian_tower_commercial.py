"""Canonical Meridian Tower commercial seed data.

Reproduces Canonical_Demo_Dataset.md sections 9-10 exactly, using this
system's own real domain state machines and use cases (never a pre-set
status) — the same discipline the Reference Engineering System's seed
script already established for RFI-214/SUB-118/ASI-07.

Scenario A (frozen, verbatim from 05_Downstream_Reference_Execution_Trace.md,
INR per ADR-016): po_4471, po_4488, po_4512.
Scenario B (Canonical_Demo_Dataset.md section 10, USD per ADR-016): po_5201,
po_5202. req_5203 is NOT seeded here — see ADR-017 (it is structurally a
PurchaseRequisition, CS-2 scope, and Canonical_Demo_Dataset.md itself states
it has no vendor).

This system shares no database with the Reference Engineering System or
Downstream (ADR-011); every identifier below is a plain business key.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from application.use_cases.commitment_use_cases import CreateCommitment
from application.use_cases.cost_code_use_cases import CreateCostCode
from application.use_cases.po_line_use_cases import (
    CreatePOLine,
    InstallPOLine,
    IssuePOLine,
    ShipPOLine,
    StartFabricationPOLine,
)
from application.use_cases.po_schedule_line_use_cases import CreatePOScheduleLine
from application.use_cases.purchase_order_use_cases import (
    AcknowledgePurchaseOrder,
    ApprovePurchaseOrder,
    CreatePurchaseOrder,
    SubmitPurchaseOrderForApproval,
)
from application.use_cases.vendor_use_cases import ApproveVendor, CreateVendor, PrequalifyVendor
from domain.state_machines import purchase_order_transitions
from domain.value_objects import OrgScope, PermissionScope
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher
from infrastructure.clock import SystemClock
from infrastructure.persistence.repositories.sqlalchemy_commitment_repository import (
    SqlAlchemyCommitmentRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_cost_code_repository import (
    SqlAlchemyCostCodeRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_purchase_order_repository import (
    SqlAlchemyPOLineRepository,
    SqlAlchemyPOScheduleLineRepository,
    SqlAlchemyPurchaseOrderRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyOAuthClientRepository,
    SqlAlchemyUserRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_vendor_repository import SqlAlchemyVendorRepository
from domain.entities.user import OAuthClient, User

# Scenario A org scope (docs/05 Phase 12.2's literal SAP fields).
SCOPE_A = OrgScope(company_code="1000", plant="P100")
# Scenario B org scope — an inferred seed choice, recorded in ADR-012 (no
# frozen document states one for Scenario B).
SCOPE_B = OrgScope(company_code="2000", plant="P200")


def seed(session: Session) -> dict:
    hasher = Pbkdf2PasswordHasher()
    clock = SystemClock()

    vendor_repo = SqlAlchemyVendorRepository(session)
    cost_code_repo = SqlAlchemyCostCodeRepository(session)
    commitment_repo = SqlAlchemyCommitmentRepository(session)
    po_repo = SqlAlchemyPurchaseOrderRepository(session)
    po_line_repo = SqlAlchemyPOLineRepository(session)
    po_schedule_line_repo = SqlAlchemyPOScheduleLineRepository(session)
    user_repo = SqlAlchemyUserRepository(session)
    oauth_client_repo = SqlAlchemyOAuthClientRepository(session)

    create_vendor = CreateVendor(vendor_repo)
    prequalify_vendor = PrequalifyVendor(vendor_repo)
    approve_vendor = ApproveVendor(vendor_repo)
    create_cost_code = CreateCostCode(cost_code_repo)
    create_commitment = CreateCommitment(commitment_repo)
    create_po = CreatePurchaseOrder(po_repo)
    submit_po = SubmitPurchaseOrderForApproval(po_repo, clock)
    approve_po = ApprovePurchaseOrder(po_repo, clock)
    acknowledge_po = AcknowledgePurchaseOrder(po_repo, clock)
    create_po_line = CreatePOLine(po_line_repo)
    issue_line = IssuePOLine(po_line_repo)
    start_fabrication_line = StartFabricationPOLine(po_line_repo)
    ship_line = ShipPOLine(po_line_repo)
    install_line = InstallPOLine(po_line_repo)  # noqa: F841 (available; no seeded line reaches "installed")
    create_po_schedule_line = CreatePOScheduleLine(po_schedule_line_repo)

    # ------------------------------------------------------------------
    # Vendors (Canonical_Demo_Dataset.md §9) — approved/qualified, since
    # each already holds a live PO in the frozen trace.
    # ------------------------------------------------------------------

    def _seeded_vendor(name: str):
        v = create_vendor.execute(name)
        v = prequalify_vendor.execute(v.id)
        v = approve_vendor.execute(v.id)
        return v

    vendorco_metals = _seeded_vendor("VendorCo Metals")
    arjun_steelworks = _seeded_vendor("Arjun Steelworks")
    thermawrap = _seeded_vendor("ThermaWrap")
    voltrex_switchgear = _seeded_vendor("Voltrex Switchgear Inc.")
    ferro_electrical = _seeded_vendor("Ferro Electrical Supply")

    # ------------------------------------------------------------------
    # Cost codes — only where a frozen document actually states one
    # (ADR-015/ADR-017: po_4488/po_4512 carry no cost code in docs/05).
    # ------------------------------------------------------------------

    cost_code_23_100 = create_cost_code.execute(
        native_code="23-100",
        cost_code_format="CSI_MASTERFORMAT",
        standard_ref="23 31 13",
        org_scope=SCOPE_A,
    )
    cost_code_26_200 = create_cost_code.execute(
        native_code="26-200",
        cost_code_format="CSI_MASTERFORMAT",
        standard_ref="26 24 13",
        org_scope=SCOPE_B,
    )

    # ------------------------------------------------------------------
    # Scenario A — "The Duct Reroute" (frozen, verbatim, INR)
    # ------------------------------------------------------------------

    po_4471 = create_po.execute(
        vendor_id=vendorco_metals.id,
        currency="INR",
        po_number="4500018823",
        org_scope=SCOPE_A,
    )
    po_4471 = submit_po.execute(po_4471.po_number)
    po_4471 = approve_po.execute(po_4471.po_number)
    po_4471 = acknowledge_po.execute(po_4471.po_number)

    line_4471 = create_po_line.execute(
        po_id=po_4471.id,
        line_no=1,
        description="Duct fabrication — DN200, Level 4 Grid B-4 reroute scope",
        quantity=1,
        uom="LOT",
        unit_price=820000,
        value=820000,
        cost_code_id=cost_code_23_100.id,
        spec_section_refs=["23 31 13"],
    )
    line_4471 = issue_line.execute(line_4471.id)
    line_4471 = start_fabrication_line.execute(line_4471.id)  # IN_FABRICATION per docs/05

    create_commitment.execute(
        source_type="PO",
        cost_code_id=cost_code_23_100.id,
        committed_amount=820000,
        currency="INR",
        po_id=po_4471.id,
        org_scope=SCOPE_A,
    )

    # po_4488 — no SAP po_number, no cost code (docs/05: both "not stated in
    # trace" / reached only via structural dependency — ADR-017). No
    # Commitment is created for this PO (ADR-015). Because it has no
    # po_number, the po_number-keyed transition use cases every other PO in
    # this seed uses don't apply — its transitions are applied directly
    # through the domain state machine and persisted through the repository.
    po_4488 = create_po.execute(vendor_id=arjun_steelworks.id, currency="INR", org_scope=SCOPE_A)
    po_4488 = po_repo.update(purchase_order_transitions.submit_for_approval(po_4488))
    po_4488 = po_repo.update(purchase_order_transitions.approve(po_4488))
    po_4488 = po_repo.update(purchase_order_transitions.acknowledge(po_4488, clock.now()))

    line_4488 = create_po_line.execute(
        po_id=po_4488.id,
        line_no=1,
        description="Hanger steel — supports duct run affected by RFI-214",
        quantity=1,
        uom="LOT",
        unit_price=610000,
        value=610000,
    )
    line_4488 = issue_line.execute(line_4488.id)
    line_4488 = start_fabrication_line.execute(line_4488.id)
    line_4488 = ship_line.execute(line_4488.id)  # SHIPPED per docs/05

    po_4512 = create_po.execute(
        vendor_id=thermawrap.id, currency="INR", po_number="4500019104", org_scope=SCOPE_A
    )
    po_4512 = submit_po.execute(po_4512.po_number)
    po_4512 = approve_po.execute(po_4512.po_number)

    line_4512 = create_po_line.execute(
        po_id=po_4512.id,
        line_no=1,
        description="Insulation — duct run, Level 4",
        quantity=1,
        uom="LOT",
        unit_price=410000,
        value=410000,
    )
    line_4512 = issue_line.execute(line_4512.id)  # SCHEDULED/"issued" per docs/05 — not yet in_fabrication

    create_po_schedule_line.execute(
        po_line_id=line_4512.id,
        schedule_no=1,
        quantity=1,
        required_on_site_date=date(2026, 8, 22),  # docs/05 Phase 5e's literal "Aug 22" date
        delivery_status="SCHEDULED",
    )

    # ------------------------------------------------------------------
    # Scenario B — "The HVAC Upsize" (Canonical_Demo_Dataset.md §10, USD)
    # ------------------------------------------------------------------

    po_5201 = create_po.execute(
        vendor_id=voltrex_switchgear.id,
        currency="USD",
        po_number="4500020045",
        org_scope=SCOPE_B,
    )
    po_5201 = submit_po.execute(po_5201.po_number)
    po_5201 = approve_po.execute(po_5201.po_number)
    po_5201 = acknowledge_po.execute(po_5201.po_number)

    line_5201 = create_po_line.execute(
        po_id=po_5201.id,
        line_no=1,
        description="Switchgear lineup — VSI-4000MV, 4000A 15kV class",
        quantity=1,
        uom="LOT",
        unit_price=42000000,
        value=42000000,
        cost_code_id=cost_code_26_200.id,
        spec_section_refs=["26 24 13"],
    )
    line_5201 = issue_line.execute(line_5201.id)
    line_5201 = start_fabrication_line.execute(line_5201.id)  # IN_FABRICATION per Canonical Dataset §10

    create_po_schedule_line.execute(
        po_line_id=line_5201.id,
        schedule_no=1,
        quantity=1,
        required_on_site_date=date(2027, 5, 15),  # Canonical_Demo_Dataset.md §13 literal date
        delivery_status="SCHEDULED",
    )

    create_commitment.execute(
        source_type="PO",
        cost_code_id=cost_code_26_200.id,
        committed_amount=42000000,
        currency="USD",
        po_id=po_5201.id,
        org_scope=SCOPE_B,
    )

    po_5202 = create_po.execute(
        vendor_id=ferro_electrical.id,
        currency="USD",
        po_number="4500020091",
        org_scope=SCOPE_B,
    )
    po_5202 = submit_po.execute(po_5202.po_number)
    po_5202 = approve_po.execute(po_5202.po_number)
    po_5202 = acknowledge_po.execute(po_5202.po_number)

    line_5202 = create_po_line.execute(
        po_id=po_5202.id,
        line_no=1,
        description="Feeder/busway — serving switchgear lineup on PO-5201",
        quantity=1,
        uom="LOT",
        unit_price=6500000,
        value=6500000,
        cost_code_id=cost_code_26_200.id,  # Canonical_Demo_Dataset.md §10's own table states this explicitly
        # spec_section_refs left empty: §13's graph reaches this PO only via
        # a structurally_depends_on edge from PO-5201, never a direct spec
        # citation of its own (mirroring the same PROBABLE-tier pattern as
        # po_4488/po_4512 in Scenario A).
    )
    line_5202 = issue_line.execute(line_5202.id)
    line_5202 = start_fabrication_line.execute(line_5202.id)
    line_5202 = ship_line.execute(line_5202.id)  # SHIPPED (in transit) per Canonical Dataset §10

    create_commitment.execute(
        source_type="PO",
        cost_code_id=cost_code_26_200.id,
        committed_amount=6500000,
        currency="USD",
        po_id=po_5202.id,
        org_scope=SCOPE_B,
    )

    # ------------------------------------------------------------------
    # Human users (approved plan §9 roles) and OAuth2 client_credentials
    # integration clients (full-scope + partial-scope, mirroring RES's
    # acting_credential_scope continuity pattern).
    # ------------------------------------------------------------------

    procurement_manager = user_repo.add(
        User(
            id=None,
            name="Ananya Rao",
            email="ananya.rao@meridiangc.example",
            role="PROCUREMENT_MANAGER",
            password_hash=hasher.hash("demo-password"),
        )
    )
    buyer = user_repo.add(
        User(
            id=None,
            name="Priya Nair",
            email="priya.nair@meridiangc.example",
            role="BUYER",
            password_hash=hasher.hash("demo-password"),
        )
    )
    admin = user_repo.add(
        User(
            id=None,
            name="System Admin",
            email="admin@downstream.example",
            role="ADMIN",
            password_hash=hasher.hash("demo-password"),
        )
    )

    full_scope_client = oauth_client_repo.add(
        OAuthClient(
            id=None,
            client_id="downstream-full-scope",
            client_secret_hash=hasher.hash("demo-client-secret"),
            company_code="1000",
            permission_scope=PermissionScope.full(),
        )
    )
    partial_scope_client = oauth_client_repo.add(
        OAuthClient(
            id=None,
            client_id="downstream-partial-scope",
            client_secret_hash=hasher.hash("demo-client-secret"),
            company_code="1000",
            permission_scope=PermissionScope.partial("purchase_orders", "vendors"),
        )
    )
    # A second-company-code client, so ADR-012's isolation guarantee has a
    # real, distinct credential to test against (not just a query filter).
    scope_b_client = oauth_client_repo.add(
        OAuthClient(
            id=None,
            client_id="downstream-scope-b",
            client_secret_hash=hasher.hash("demo-client-secret"),
            company_code="2000",
            permission_scope=PermissionScope.full(),
        )
    )

    return {
        "vendors": 5,
        "cost_codes": 2,
        "purchase_orders": 5,
        "po_lines": 5,
        "po_schedule_lines": 2,
        "commitments": 3,
        "users": 3,
        "oauth_clients": 3,
        "scenario_a_pos": [po_4471.po_number, po_4488.po_number, po_4512.po_number],
        "scenario_b_pos": [po_5201.po_number, po_5202.po_number],
    }
