from __future__ import annotations

from domain.entities.purchase_order import POLine
from domain.repositories.purchase_order_repository import POLineRepository
from domain.state_machines import po_line_transitions as txn

from application.exceptions import NotFound


class CreatePOLine:
    def __init__(self, repo: POLineRepository) -> None:
        self._repo = repo

    def execute(
        self,
        po_id: int,
        line_no: int,
        description: str,
        quantity: float,
        uom: str,
        unit_price: float,
        value: float,
        cost_code_id: int | None = None,
        spec_section_refs: list[str] | None = None,
        lifecycle_position: str = "draft",
    ) -> POLine:
        return self._repo.add(
            POLine(
                id=None,
                po_id=po_id,
                line_no=line_no,
                description=description,
                quantity=quantity,
                uom=uom,
                unit_price=unit_price,
                value=value,
                cost_code_id=cost_code_id,
                spec_section_refs=spec_section_refs or [],
                lifecycle_position=lifecycle_position,
            )
        )


class ListPOLines:
    def __init__(self, repo: POLineRepository) -> None:
        self._repo = repo

    def execute(self, po_id: int) -> list[POLine]:
        return self._repo.list_by_po(po_id)


class GetPOLine:
    def __init__(self, repo: POLineRepository) -> None:
        self._repo = repo

    def execute(self, line_id: int) -> POLine:
        line = self._repo.get(line_id)
        if line is None:
            raise NotFound("POLine", line_id)
        return line


class _POLineTransitionUseCase:
    _transition = staticmethod(lambda line: line)

    def __init__(self, repo: POLineRepository) -> None:
        self._repo = repo

    def execute(self, line_id: int) -> POLine:
        line = self._repo.get(line_id)
        if line is None:
            raise NotFound("POLine", line_id)
        updated = self._transition(line)
        return self._repo.update(updated)


class IssuePOLine(_POLineTransitionUseCase):
    _transition = staticmethod(txn.issue_line)


class StartFabricationPOLine(_POLineTransitionUseCase):
    _transition = staticmethod(txn.start_fabrication)


class ShipPOLine(_POLineTransitionUseCase):
    _transition = staticmethod(txn.ship)


class InstallPOLine(_POLineTransitionUseCase):
    _transition = staticmethod(txn.install)
