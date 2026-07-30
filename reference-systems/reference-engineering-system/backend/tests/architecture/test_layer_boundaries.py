from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"

# Modules a given layer's own code is forbidden from importing, checked by
# parsing every file's import statements rather than trusting convention —
# "business rules must never depend on FastAPI" as a checked fact.
FORBIDDEN_IMPORTS = {
    "domain": {"fastapi", "sqlalchemy", "httpx", "jwt", "pydantic_settings", "api", "infrastructure", "application"},
    "application": {"fastapi", "sqlalchemy", "httpx", "jwt", "pydantic_settings", "api", "infrastructure"},
}


def _imported_top_level_modules(file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module.split(".")[0])
    return modules


def test_domain_and_application_never_import_forbidden_modules():
    violations = []
    for layer, forbidden in FORBIDDEN_IMPORTS.items():
        layer_dir = SRC / layer
        for py_file in layer_dir.rglob("*.py"):
            found = _imported_top_level_modules(py_file) & forbidden
            if found:
                violations.append(f"{py_file.relative_to(SRC)} imports forbidden: {found}")
    assert not violations, "\n".join(violations)
