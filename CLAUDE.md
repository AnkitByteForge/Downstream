# Downstream Development Rules

## Mission

Build Downstream exactly according to the documents in /docs.

The architecture is frozen.

Never redesign it unless explicitly instructed.

---

## Source of Truth

Always read these documents before making changes.

1. 01_Downstream_The_Company.md
2. 02_Downstream_Product_Design.md
3. 03_Downstream_Systems_Architecture.md
4. 04_Downstream_Connector_Layer_Validation.md
5. 05_Downstream_Reference_Execution_Trace.md
6. 06_Downstream_Implementation_Backlog.md
7. 07_Downstream_Implementation_Blueprint.md

---

## Rules

Do not invent features.

Do not invent services.

Do not invent APIs.

Do not change event names.

Do not change service boundaries.

Follow the implementation blueprint.

Implement only the milestone requested.

Keep every service independent.

Use FastAPI.

Use PostgreSQL.

Use Neo4j.

Use Kafka.

Use Docker Compose.

Every service must be runnable independently.

Every commit should leave the repository runnable.

Never implement future milestones unless explicitly requested.
