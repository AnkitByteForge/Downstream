"""Streaming file hashing — never loads a source PDF fully into memory.

A 250MB+ file must be hashed in fixed-size chunks; `hashlib` on the whole
`Path.read_bytes()` output would defeat the entire point of Phase A's
"no giant in-memory PDF loading" requirement before pypdfium2 is even
opened.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

_CHUNK_SIZE = 1024 * 1024  # 1 MiB


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()
