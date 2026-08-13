from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from application.ports import ClockPort
from domain.entities.commitment import Commitment
from domain.entities.contract import Contract
from domain.entities.cost_code import CostCode
from domain.entities.purchase_order import POLine, POScheduleLine, PurchaseOrder
from domain.entities.user import OAuthClient, OAuthToken, User
from domain.entities.vendor import Vendor, VendorScopeView
from domain.repositories.commitment_repository import CommitmentRepository
from domain.repositories.contract_repository import ContractRepository
from domain.repositories.cost_code_repository import CostCodeRepository
from domain.repositories.purchase_order_repository import (
    POLineRepository,
    POScheduleLineRepository,
    PurchaseOrderRepository,
)
from domain.repositories.user_repository import OAuthClientRepository, OAuthTokenRepository, UserRepository
from domain.repositories.vendor_repository import VendorRepository, VendorScopeViewRepository


class FakeClock(ClockPort):
    def __init__(self, fixed: datetime | None = None) -> None:
        self._fixed = fixed or datetime(2026, 7, 30, 0, 0, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._fixed


class InMemoryVendorRepository(VendorRepository):
    def __init__(self) -> None:
        self._rows: dict[int, Vendor] = {}
        self._next_id = 1

    def add(self, vendor: Vendor) -> Vendor:
        vendor = replace(vendor, id=self._next_id)
        self._rows[vendor.id] = vendor
        self._next_id += 1
        return vendor

    def get(self, vendor_id: int) -> Vendor | None:
        return self._rows.get(vendor_id)

    def list_all(self) -> list[Vendor]:
        return list(self._rows.values())

    def update(self, vendor: Vendor) -> Vendor:
        self._rows[vendor.id] = vendor
        return vendor


class InMemoryVendorScopeViewRepository(VendorScopeViewRepository):
    def __init__(self) -> None:
        self._rows: dict[int, VendorScopeView] = {}
        self._next_id = 1

    def add(self, scope_view: VendorScopeView) -> VendorScopeView:
        scope_view = replace(scope_view, id=self._next_id)
        self._rows[scope_view.id] = scope_view
        self._next_id += 1
        return scope_view

    def list_by_vendor(self, vendor_id: int) -> list[VendorScopeView]:
        return [v for v in self._rows.values() if v.vendor_id == vendor_id]


class InMemoryCostCodeRepository(CostCodeRepository):
    def __init__(self) -> None:
        self._rows: dict[int, CostCode] = {}
        self._next_id = 1

    def add(self, cost_code: CostCode) -> CostCode:
        cost_code = replace(cost_code, id=self._next_id)
        self._rows[cost_code.id] = cost_code
        self._next_id += 1
        return cost_code

    def get(self, cost_code_id: int) -> CostCode | None:
        return self._rows.get(cost_code_id)

    def get_by_native_code(self, native_code: str) -> CostCode | None:
        for c in self._rows.values():
            if c.native_code == native_code:
                return c
        return None

    def list_all(self) -> list[CostCode]:
        return list(self._rows.values())


class InMemoryContractRepository(ContractRepository):
    def __init__(self) -> None:
        self._rows: dict[int, Contract] = {}
        self._next_id = 1

    def add(self, contract: Contract) -> Contract:
        contract = replace(contract, id=self._next_id)
        self._rows[contract.id] = contract
        self._next_id += 1
        return contract

    def get(self, contract_id: int) -> Contract | None:
        return self._rows.get(contract_id)

    def list_all(self) -> list[Contract]:
        return list(self._rows.values())


class InMemoryCommitmentRepository(CommitmentRepository):
    def __init__(self) -> None:
        self._rows: dict[int, Commitment] = {}
        self._next_id = 1

    def add(self, commitment: Commitment) -> Commitment:
        commitment = replace(commitment, id=self._next_id)
        self._rows[commitment.id] = commitment
        self._next_id += 1
        return commitment

    def get(self, commitment_id: int) -> Commitment | None:
        return self._rows.get(commitment_id)

    def list_all(self) -> list[Commitment]:
        return list(self._rows.values())

    def update(self, commitment: Commitment) -> Commitment:
        self._rows[commitment.id] = commitment
        return commitment


class InMemoryPurchaseOrderRepository(PurchaseOrderRepository):
    def __init__(self) -> None:
        self._rows: dict[int, PurchaseOrder] = {}
        self._next_id = 1

    def add(self, po: PurchaseOrder) -> PurchaseOrder:
        po = replace(po, id=self._next_id)
        self._rows[po.id] = po
        self._next_id += 1
        return po

    def get(self, po_id: int) -> PurchaseOrder | None:
        return self._rows.get(po_id)

    def get_by_po_number(self, po_number: str) -> PurchaseOrder | None:
        for po in self._rows.values():
            if po.po_number == po_number:
                return po
        return None

    def list_all(self) -> list[PurchaseOrder]:
        return list(self._rows.values())

    def list_changed_since(self, since: datetime) -> list[PurchaseOrder]:
        return [po for po in self._rows.values() if po.changed_at is not None and po.changed_at >= since]

    def update(self, po: PurchaseOrder) -> PurchaseOrder:
        self._rows[po.id] = po
        return po


class InMemoryPOLineRepository(POLineRepository):
    def __init__(self) -> None:
        self._rows: dict[int, POLine] = {}
        self._next_id = 1

    def add(self, line: POLine) -> POLine:
        line = replace(line, id=self._next_id)
        self._rows[line.id] = line
        self._next_id += 1
        return line

    def get(self, line_id: int) -> POLine | None:
        return self._rows.get(line_id)

    def list_by_po(self, po_id: int) -> list[POLine]:
        return [line for line in self._rows.values() if line.po_id == po_id]

    def update(self, line: POLine) -> POLine:
        self._rows[line.id] = line
        return line


class InMemoryPOScheduleLineRepository(POScheduleLineRepository):
    def __init__(self) -> None:
        self._rows: dict[int, POScheduleLine] = {}
        self._next_id = 1

    def add(self, schedule_line: POScheduleLine) -> POScheduleLine:
        schedule_line = replace(schedule_line, id=self._next_id)
        self._rows[schedule_line.id] = schedule_line
        self._next_id += 1
        return schedule_line

    def get(self, schedule_line_id: int) -> POScheduleLine | None:
        return self._rows.get(schedule_line_id)

    def list_by_po_line(self, po_line_id: int) -> list[POScheduleLine]:
        return [sl for sl in self._rows.values() if sl.po_line_id == po_line_id]


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._rows: dict[int, User] = {}
        self._next_id = 1

    def add(self, user: User) -> User:
        user = replace(user, id=self._next_id)
        self._rows[user.id] = user
        self._next_id += 1
        return user

    def get(self, user_id: int) -> User | None:
        return self._rows.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        for u in self._rows.values():
            if u.email == email:
                return u
        return None


class InMemoryOAuthClientRepository(OAuthClientRepository):
    def __init__(self) -> None:
        self._rows: dict[str, OAuthClient] = {}
        self._next_id = 1

    def add(self, client: OAuthClient) -> OAuthClient:
        client = replace(client, id=self._next_id)
        self._rows[client.client_id] = client
        self._next_id += 1
        return client

    def get_by_client_id(self, client_id: str) -> OAuthClient | None:
        return self._rows.get(client_id)


class InMemoryOAuthTokenRepository(OAuthTokenRepository):
    def __init__(self) -> None:
        self._rows: dict[str, OAuthToken] = {}
        self._next_id = 1

    def add(self, token: OAuthToken) -> OAuthToken:
        token = replace(token, id=self._next_id)
        self._rows[token.access_token] = token
        self._next_id += 1
        return token

    def get_by_access_token(self, access_token: str) -> OAuthToken | None:
        return self._rows.get(access_token)
