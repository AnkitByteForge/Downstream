from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.purchase_order import POLine, POScheduleLine, PurchaseOrder


class PurchaseOrderRepository(ABC):
    @abstractmethod
    def add(self, po: PurchaseOrder) -> PurchaseOrder: ...

    @abstractmethod
    def get(self, po_id: int) -> PurchaseOrder | None: ...

    @abstractmethod
    def get_by_po_number(self, po_number: str) -> PurchaseOrder | None: ...

    @abstractmethod
    def list_all(self) -> list[PurchaseOrder]: ...

    @abstractmethod
    def list_changed_since(self, since: datetime) -> list[PurchaseOrder]: ...

    @abstractmethod
    def update(self, po: PurchaseOrder) -> PurchaseOrder: ...


class POLineRepository(ABC):
    @abstractmethod
    def add(self, line: POLine) -> POLine: ...

    @abstractmethod
    def get(self, line_id: int) -> POLine | None: ...

    @abstractmethod
    def list_by_po(self, po_id: int) -> list[POLine]: ...

    @abstractmethod
    def update(self, line: POLine) -> POLine: ...


class POScheduleLineRepository(ABC):
    @abstractmethod
    def add(self, schedule_line: POScheduleLine) -> POScheduleLine: ...

    @abstractmethod
    def get(self, schedule_line_id: int) -> POScheduleLine | None: ...

    @abstractmethod
    def list_by_po_line(self, po_line_id: int) -> list[POScheduleLine]: ...
