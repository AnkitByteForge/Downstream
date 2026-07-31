from __future__ import annotations

from api.pagination import PageParams, paginate


def _params(page: int = 1, per_page: int = 20) -> PageParams:
    return PageParams(page=page, per_page=per_page)


def test_paginate_first_page():
    items = list(range(1, 51))
    page, total = paginate(items, _params(page=1, per_page=20))
    assert page == list(range(1, 21))
    assert total == 50


def test_paginate_last_partial_page():
    items = list(range(1, 51))
    page, total = paginate(items, _params(page=3, per_page=20))
    assert page == list(range(41, 51))
    assert total == 50


def test_paginate_page_beyond_range_is_empty_but_total_is_accurate():
    items = list(range(1, 11))
    page, total = paginate(items, _params(page=5, per_page=20))
    assert page == []
    assert total == 10
