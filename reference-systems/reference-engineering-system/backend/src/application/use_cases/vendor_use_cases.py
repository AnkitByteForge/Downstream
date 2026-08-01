from __future__ import annotations

from domain.entities.vendor import Vendor
from domain.repositories.vendor_repository import VendorRepository


class ListVendors:
    def __init__(self, repo: VendorRepository) -> None:
        self._repo = repo

    def execute(self, project_id: int) -> list[Vendor]:
        return self._repo.list_by_project(project_id)
