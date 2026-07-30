from __future__ import annotations

from domain.value_objects import PermissionScope


def test_full_scope_grants_everything():
    scope = PermissionScope.full()
    assert scope.grants("rfis")
    assert scope.grants("anything")
    assert scope.as_wire_value() == "full"


def test_partial_scope_only_grants_listed_resource_types():
    scope = PermissionScope.partial("rfis", "submittals", "documents")
    assert scope.grants("rfis")
    assert scope.grants("documents")
    assert not scope.grants("spec_sections")
    assert scope.as_wire_value() == "partial:[documents,rfis,submittals]"
