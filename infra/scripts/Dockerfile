# Shared image for Milestone 0's one-shot bootstrap scripts
# (provision_kafka_topics.py, seed_graph.py, register_res_webhook.py).
# Not a Downstream service — infra tooling only, run once per fresh
# environment by infra/docker-compose.yml's one-shot init services.
FROM python:3.11-slim

WORKDIR /scripts
COPY infra/scripts/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY infra/scripts/*.py .
