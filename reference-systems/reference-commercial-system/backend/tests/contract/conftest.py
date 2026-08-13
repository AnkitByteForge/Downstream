from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from application.ports import SessionClaims
from domain.entities.commitment import Commitment
from domain.entities.cost_code import CostCode
from domain.entities.purchase_order import POLine, PurchaseOrder
from domain.entities.user import OAuthClient, OAuthToken, User
from domain.entities.vendor import Vendor
from domain.value_objects import OrgScope, PermissionScope
from infrastructure.auth.jwt_service import JwtSessionTokenService
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher
from infrastructure.config import settings
from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.orm_models import (
    CommitmentModel,
    CostCodeModel,
    OAuthClientModel,
    OAuthTokenModel,
    POLineModel,
    PurchaseOrderModel,
    UserModel,
    VendorModel,
)
from infrastructure.persistence.repositories.sqlalchemy_commitment_repository import (
    SqlAlchemyCommitmentRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_cost_code_repository import (
    SqlAlchemyCostCodeRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_purchase_order_repository import (
    SqlAlchemyPOLineRepository,
    SqlAlchemyPurchaseOrderRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyOAuthClientRepository,
    SqlAlchemyOAuthTokenRepository,
    SqlAlchemyUserRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_vendor_repository import SqlAlchemyVendorRepository


@pytest.fixture()
def cs_contract_fixture():
    """Real, committed rows — contract tests exercise the full app (real
    Postgres, real HTTP client via TestClient), so nothing here is an
    in-process rollback trick. Two distinct company_code scopes (1000,
    2000) are seeded deliberately so org-scope isolation (ADR-012) has a
    real credential-level boundary to test, not just a query filter.
    Teardown deletes every row this fixture created."""
    session = SessionLocal()
    hasher = Pbkdf2PasswordHasher()
    try:
        vendor_repo = SqlAlchemyVendorRepository(session)
        cost_code_repo = SqlAlchemyCostCodeRepository(session)
        po_repo = SqlAlchemyPurchaseOrderRepository(session)
        line_repo = SqlAlchemyPOLineRepository(session)
        commitment_repo = SqlAlchemyCommitmentRepository(session)
        user_repo = SqlAlchemyUserRepository(session)
        client_repo = SqlAlchemyOAuthClientRepository(session)
        token_repo = SqlAlchemyOAuthTokenRepository(session)

        vendor_a = vendor_repo.add(Vendor(id=None, name="Contract Test Vendor A"))
        vendor_b = vendor_repo.add(Vendor(id=None, name="Contract Test Vendor B"))

        cost_code_a = cost_code_repo.add(
            CostCode(
                id=None,
                native_code="CT-100",
                cost_code_format="CSI_MASTERFORMAT",
                standard_ref="23 31 13",
                org_scope=OrgScope(company_code="1000", plant="P100"),
            )
        )
        cost_code_b = cost_code_repo.add(
            CostCode(
                id=None,
                native_code="CT-200",
                cost_code_format="CSI_MASTERFORMAT",
                standard_ref="26 24 13",
                org_scope=OrgScope(company_code="2000", plant="P200"),
            )
        )

        po_a = po_repo.add(
            PurchaseOrder(
                id=None,
                po_number="CT-PO-A",
                vendor_id=vendor_a.id,
                currency="INR",
                org_scope=OrgScope(company_code="1000", plant="P100"),
            )
        )
        po_b = po_repo.add(
            PurchaseOrder(
                id=None,
                po_number="CT-PO-B",
                vendor_id=vendor_b.id,
                currency="USD",
                org_scope=OrgScope(company_code="2000", plant="P200"),
            )
        )

        line_a = line_repo.add(
            POLine(
                id=None,
                po_id=po_a.id,
                line_no=1,
                description="Contract test line A",
                quantity=1,
                uom="EA",
                unit_price=100,
                value=100,
                cost_code_id=cost_code_a.id,
            )
        )

        commitment_a = commitment_repo.add(
            Commitment(
                id=None,
                source_type="PO",
                cost_code_id=cost_code_a.id,
                po_id=po_a.id,
                committed_amount=100,
                currency="INR",
                org_scope=OrgScope(company_code="1000"),
            )
        )

        human = user_repo.add(
            User(
                id=None,
                name="Contract Test User",
                email="contract.test@example.com",
                role="PROCUREMENT_MANAGER",
                password_hash=hasher.hash("irrelevant"),
            )
        )
        session_tokens = JwtSessionTokenService(settings)
        human_cookie = session_tokens.issue(SessionClaims(user_id=human.id, role="PROCUREMENT_MANAGER"))

        full_scope_client = client_repo.add(
            OAuthClient(
                id=None,
                client_id="contract-test-full-scope-a",
                client_secret_hash=hasher.hash("secret"),
                company_code="1000",
                permission_scope=PermissionScope.full(),
            )
        )
        partial_scope_client = client_repo.add(
            OAuthClient(
                id=None,
                client_id="contract-test-partial-scope-a",
                client_secret_hash=hasher.hash("secret"),
                company_code="1000",
                permission_scope=PermissionScope.partial("purchase_orders", "vendors"),
            )
        )
        full_scope_client_b = client_repo.add(
            OAuthClient(
                id=None,
                client_id="contract-test-full-scope-b",
                client_secret_hash=hasher.hash("secret"),
                company_code="2000",
                permission_scope=PermissionScope.full(),
            )
        )

        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        token_full_a = token_repo.add(
            OAuthToken(id=None, access_token="ct-token-full-a", client_id=full_scope_client.client_id, expires_at=expires)
        )
        token_partial_a = token_repo.add(
            OAuthToken(
                id=None,
                access_token="ct-token-partial-a",
                client_id=partial_scope_client.client_id,
                expires_at=expires,
            )
        )
        token_full_b = token_repo.add(
            OAuthToken(
                id=None,
                access_token="ct-token-full-b",
                client_id=full_scope_client_b.client_id,
                expires_at=expires,
            )
        )

        session.commit()

        yield {
            "vendor_a_id": vendor_a.id,
            "vendor_b_id": vendor_b.id,
            "cost_code_a_id": cost_code_a.id,
            "cost_code_b_id": cost_code_b.id,
            "po_a_number": po_a.po_number,
            "po_b_number": po_b.po_number,
            "po_a_id": po_a.id,
            "line_a_id": line_a.id,
            "commitment_a_id": commitment_a.id,
            "human_cookie": human_cookie,
            "token_full_a": token_full_a.access_token,
            "token_partial_a": token_partial_a.access_token,
            "token_full_b": token_full_b.access_token,
        }
    finally:
        # Explicit, ordered teardown respecting FK dependencies.
        session.execute(OAuthTokenModel.__table__.delete().where(OAuthTokenModel.client_id.like("contract-test-%")))
        session.execute(OAuthClientModel.__table__.delete().where(OAuthClientModel.client_id.like("contract-test-%")))
        session.execute(UserModel.__table__.delete().where(UserModel.email == "contract.test@example.com"))
        session.execute(CommitmentModel.__table__.delete().where(CommitmentModel.id == commitment_a.id))
        session.execute(POLineModel.__table__.delete().where(POLineModel.id == line_a.id))
        session.execute(
            PurchaseOrderModel.__table__.delete().where(PurchaseOrderModel.id.in_([po_a.id, po_b.id]))
        )
        session.execute(
            CostCodeModel.__table__.delete().where(CostCodeModel.id.in_([cost_code_a.id, cost_code_b.id]))
        )
        session.execute(VendorModel.__table__.delete().where(VendorModel.id.in_([vendor_a.id, vendor_b.id])))
        session.commit()
        session.close()
