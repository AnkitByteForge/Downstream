# Build context is the repo root (infra/docker-compose.yml sets
# `context: ..` + `dockerfile: apps/connector-procore/Dockerfile`), so this
# service can COPY the shared packages/ it depends on. This is also the fix
# for the pre-existing apps/* build-context bug (IMPLEMENTATION_STATUS.md
# §10.7): the old `build: ./apps/connector-procore` shorthand resolved
# relative to infra/ (this compose file's own directory) under plain
# invocation, giving the nonexistent path infra/apps/connector-procore.
FROM python:3.11-slim

WORKDIR /app

# Shared contract this service depends on (Milestone 0 package).
COPY packages/envelope-schemas /app/packages/envelope-schemas

COPY apps/connector-procore/src /app/apps/connector-procore/src

# Runtime deps installed directly (mirrors apps/connector-procore/pyproject.toml's
# [project.dependencies]) rather than via `pip install -e .`: this app's own
# modules (config/, client/, mapper/, repository/, idempotency/, inbound/)
# have no __init__.py and are run as plain Python namespace packages via
# PYTHONPATH, the same convention the repo's own root pyproject.toml already
# uses for packages/* under pytest — not packaged/installed as a distribution.
RUN pip install --no-cache-dir \
    "fastapi>=0.115,<1" \
    "uvicorn[standard]>=0.30,<1" \
    "httpx>=0.27,<1" \
    "psycopg[binary]>=3.1,<4" \
    "pydantic-settings>=2,<3" \
    /app/packages/envelope-schemas

ENV PYTHONPATH=/app/apps/connector-procore/src
WORKDIR /app/apps/connector-procore/src

EXPOSE 8080
CMD ["uvicorn", "inbound.app:app", "--host", "0.0.0.0", "--port", "8080"]
