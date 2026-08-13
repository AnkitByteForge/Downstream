#!/bin/sh
# Applies every *.sql file under the mounted migration directories, in
# sorted order, against operational-db. Run once per fresh environment by
# the `db-migrate` one-shot service in infra/docker-compose.yml.
#
# Plain numbered SQL files + psql, not Alembic: no frozen document mandates
# a migration framework for Downstream's own services (docs/07 §6 itself
# gives every table as a plain CREATE TABLE block), and every statement here
# is IF NOT EXISTS / idempotent, so re-running this script against an
# already-migrated database is safe.
set -eu

: "${PGHOST:=operational-db}"
: "${PGPORT:=5432}"
: "${PGUSER:=postgres}"
: "${PGDATABASE:=downstream_operational}"

echo "Applying migrations against ${PGDATABASE}@${PGHOST}:${PGPORT} ..."

for dir in /migrations/00-infra /migrations/10-ingestion-service /migrations/20-connector-procore /migrations/90-seed; do
    if [ -d "$dir" ]; then
        for f in "$dir"/*.sql; do
            [ -e "$f" ] || continue
            echo "  -> $f"
            psql -v ON_ERROR_STOP=1 -f "$f"
        done
    fi
done

echo "Migrations complete."
