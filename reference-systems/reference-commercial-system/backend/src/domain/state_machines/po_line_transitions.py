from __future__ import annotations

from dataclasses import replace

from domain.entities.purchase_order import POLine
from domain.exceptions import InvalidTransition

# ADR-011 / The Reference Commercial System.md §M item 3 & Recommendation #2:
# draft -> issued -> in_fabrication -> shipped -> installed, strictly
# sequential — "the single most valuable realism feature for demonstrating
# engineering-to-commercial impact, because impact severity scales with
# lifecycle position."

_ORDER = ("draft", "issued", "in_fabrication", "shipped", "installed")


def _advance(line: POLine, expected_current: str, target: str) -> POLine:
    if line.lifecycle_position != expected_current:
        raise InvalidTransition("POLine", line.lifecycle_position, target)
    return replace(line, lifecycle_position=target)


def issue_line(line: POLine) -> POLine:
    return _advance(line, "draft", "issued")


def start_fabrication(line: POLine) -> POLine:
    return _advance(line, "issued", "in_fabrication")


def ship(line: POLine) -> POLine:
    return _advance(line, "in_fabrication", "shipped")


def install(line: POLine) -> POLine:
    return _advance(line, "shipped", "installed")
