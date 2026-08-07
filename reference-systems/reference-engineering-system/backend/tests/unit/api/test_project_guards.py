from __future__ import annotations

import pytest
from fastapi import HTTPException

from api.deps import ActingContext, ensure_resource_in_project
from domain.value_objects import PermissionScope


def _human(project_id: int = 1) -> ActingContext:
    return ActingContext(kind="human", project_id=project_id, user_id=7, role="ADMIN")


def _integration(project_id: int = 1, scope: PermissionScope | None = None) -> ActingContext:
    return ActingContext(
        kind="integration",
        project_id=project_id,
        permission_scope=scope or PermissionScope.full(),
    )


def test_human_same_project_require_project_passes():
    _human(1).require_project(1)  # must not raise


def test_human_cross_project_require_project_404():
    with pytest.raises(HTTPException) as exc:
        _human(1).require_project(2)
    assert exc.value.status_code == 404


def test_integration_cross_project_require_project_404():
    with pytest.raises(HTTPException) as exc:
        _integration(1).require_project(2)
    assert exc.value.status_code == 404


def test_integration_same_project_require_project_passes():
    _integration(3).require_project(3)  # must not raise


def test_ensure_resource_in_project_passes_on_match():
    ensure_resource_in_project(5, 5)  # must not raise


def test_ensure_resource_in_project_404_on_mismatch():
    with pytest.raises(HTTPException) as exc:
        ensure_resource_in_project(1, 2)
    assert exc.value.status_code == 404


def test_ensure_resource_in_project_404_on_none():
    with pytest.raises(HTTPException) as exc:
        ensure_resource_in_project(None, 2)
    assert exc.value.status_code == 404
