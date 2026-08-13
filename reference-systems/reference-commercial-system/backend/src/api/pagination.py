from __future__ import annotations

from typing import TypeVar

from fastapi import Query

T = TypeVar("T")

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


class PageParams:
    """docs/04's per_page/page pagination requirement, reproduced from the
    Reference Engineering System's own convention for consistency across
    both reference systems (independent code, matching pattern)."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE),
    ) -> None:
        self.page = page
        self.per_page = per_page


def paginate(items: list[T], params: PageParams) -> tuple[list[T], int]:
    total = len(items)
    start = (params.page - 1) * params.per_page
    end = start + params.per_page
    return items[start:end], total
