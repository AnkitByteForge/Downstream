from __future__ import annotations

import uvicorn

from config.settings import settings
from inbound.app import app  # noqa: F401 - imported for uvicorn's benefit below

if __name__ == "__main__":
    uvicorn.run("inbound.app:app", host=settings.host, port=settings.port)
