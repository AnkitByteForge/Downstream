# Build context is the repo root (infra/docker-compose.yml sets
# `context: ..` + `dockerfile: apps/key-resolution-service/Dockerfile`) —
# same apps/* build-context fix pattern already applied to
# connector-procore/ingestion-service in Milestone 1.
FROM python:3.11-slim

WORKDIR /app

COPY packages/event-contracts /app/packages/event-contracts
COPY packages/domain-models /app/packages/domain-models
COPY packages/envelope-schemas /app/packages/envelope-schemas

COPY apps/key-resolution-service/src /app/apps/key-resolution-service/src

RUN pip install --no-cache-dir \
    "psycopg[binary]>=3.1,<4" \
    "pydantic-settings>=2,<3" \
    "kafka-python-ng>=2.2,<3" \
    "neo4j>=5,<6" \
    /app/packages/envelope-schemas \
    /app/packages/domain-models \
    /app/packages/event-contracts

ENV PYTHONPATH=/app/apps/key-resolution-service/src
WORKDIR /app/apps/key-resolution-service/src

CMD ["python", "main.py"]
