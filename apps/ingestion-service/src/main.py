from __future__ import annotations

import uvicorn

from api.app import app  # noqa: F401
from config.settings import settings

if __name__ == "__main__":
    uvicorn.run("api.app:app", host=settings.host, port=settings.port)
