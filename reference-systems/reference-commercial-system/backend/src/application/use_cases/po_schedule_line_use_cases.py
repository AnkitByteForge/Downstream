from __future__ import annotations

from datetime import date

from domain.entities.purchase_order import POScheduleLine
from domain.repositories.purchase_order_repository import POScheduleLineRepository

from application.exceptions import NotFound


class CreatePOScheduleLine:
    def __init__(self, repo: POScheduleLineRepository) -> None:
        self._repo = repo

    def execute(
        self,
        po_line_id: int,
        schedule_no: int,
        quantity: float,
        required_on_site_date: date | None = None,
        promised_date: date | None = None,
        linked_schedule_activity_ref: str | None = None,
        delivery_status: str = "SCHEDULED",
    ) -> POScheduleLine:
        return self._repo.add(
            POScheduleLine(
                id=None,
                po_line_id=po_line_id,
                schedule_no=schedule_no,
                quantity=quantity,
                required_on_site_date=required_on_site_date,
                promised_date=promised_date,
                linked_schedule_activity_ref=linked_schedule_activity_ref,
                delivery_status=delivery_status,
            )
        )


class ListPOScheduleLines:
    def __init__(self, repo: POScheduleLineRepository) -> None:
        self._repo = repo

    def execute(self, po_line_id: int) -> list[POScheduleLine]:
        return self._repo.list_by_po_line(po_line_id)


class GetPOScheduleLine:
    def __init__(self, repo: POScheduleLineRepository) -> None:
        self._repo = repo

    def execute(self, schedule_line_id: int) -> POScheduleLine:
        line = self._repo.get(schedule_line_id)
        if line is None:
            raise NotFound("POScheduleLine", schedule_line_id)
        return line
