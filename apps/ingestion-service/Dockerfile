# Build context is the repo root (infra/docker-compose.yml sets
# `context: ..` + `dockerfile: apps/ingestion-service/Dockerfile`) — see
# apps/connector-procore/Dockerfile's header comment for why (the apps/*
# build-context fix).
FROM python:3.11-slim

WORKDIR /app

COPY packages/envelope-schemas /app/packages/envelope-schemas
COPY packages/domain-models /app/packages/domain-models
COPY packages/event-contracts /app/packages/event-contracts
COPY packages/shared-config /app/packages/shared-config

COPY apps/ingestion-service/src /app/apps/ingestion-service/src

RUN pip install --no-cache-dir \
    "fastapi>=0.115,<1" \
    "uvicorn[standard]>=0.30,<1" \
    "psycopg[binary]>=3.1,<4" \
    "pydantic-settings>=2,<3" \
    "kafka-python-ng>=2.2,<3" \
    /app/packages/envelope-schemas \
    /app/packages/domain-models \
    /app/packages/event-contracts \
    /app/packages/shared-config

ENV PYTHONPATH=/app/apps/ingestion-service/src
WORKDIR /app/apps/ingestion-service/src

EXPOSE 8100
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8100"]
