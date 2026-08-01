from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.submittal import (
    Submittal,
    SubmittalPackage,
    SubmittalRequirement,
    SubmittalReviewStatus,
    SubmittalRevision,
)


class SubmittalPackageRepository(ABC):
    @abstractmethod
    def add(self, package: SubmittalPackage) -> SubmittalPackage: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[SubmittalPackage]: ...


class SubmittalReviewStatusRepository(ABC):
    @abstractmethod
    def add(self, status: SubmittalReviewStatus) -> SubmittalReviewStatus: ...

    @abstractmethod
    def get(self, status_id: int) -> SubmittalReviewStatus | None: ...

    @abstractmethod
    def get_by_code(self, project_id: int, code: str) -> SubmittalReviewStatus | None: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[SubmittalReviewStatus]: ...


class SubmittalRequirementRepository(ABC):
    @abstractmethod
    def add(self, requirement: SubmittalRequirement) -> SubmittalRequirement: ...

    @abstractmethod
    def list_by_project(
        self, project_id: int, spec_section_id: int | None = None
    ) -> list[SubmittalRequirement]: ...


class SubmittalRepository(ABC):
    @abstractmethod
    def add(self, submittal: Submittal) -> Submittal: ...

    @abstractmethod
    def get(self, submittal_id: int) -> Submittal | None: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[Submittal]: ...


class SubmittalRevisionRepository(ABC):
    @abstractmethod
    def add(self, revision: SubmittalRevision) -> SubmittalRevision: ...

    @abstractmethod
    def update(self, revision: SubmittalRevision) -> SubmittalRevision: ...

    @abstractmethod
    def get(self, revision_id: int) -> SubmittalRevision | None: ...

    @abstractmethod
    def list_by_submittal(self, submittal_id: int) -> list[SubmittalRevision]: ...
