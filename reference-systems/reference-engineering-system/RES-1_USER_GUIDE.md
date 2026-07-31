# RES-1 — User Guide

**Scope of this document:** how to run, log into, and exercise the Reference
Engineering System as it stands at RES-1 (see root `IMPLEMENTATION_STATUS.md`
§10 for the full build record). This is a practical run/test guide, not a
design document — if anything here disagrees with `docs/`, `docs/` wins.

---

## 1. What RES-1 actually is

The Reference Engineering System is **not** a Downstream service. It plays
the role of the external system (a Procore/ACC-shaped construction
engineering platform) that a future `connector-procore` will connect into.
It exists so Downstream's connector layer has something real and
vendor-realistic to ingest from, instead of a hand-waved mock.

RES-1 is the **first of five** planned milestones for this subsystem. It
implements:

- 7 of the ~15 entity types named in `docs/reference/The Reference
  Engineering System.md`: Project, Discipline, Location, SpecSection,
  Drawing, DrawingVersion, RFI.
- 2 of its 6 state machines: RFI (`DRAFT → OPEN → RESPONDED → CLOSED`) and
  DrawingVersion (`DRAFT → ISSUED → REVISED → SUPERSEDED`).
- Two auth surfaces: human session login (what you use in the browser) and
  OAuth2 for integration clients (what a connector would use).
- One seeded scenario: the Meridian Tower / RFI-214 story from
  `docs/05_Downstream_Reference_Execution_Trace.md`, reproduced field-for-field.

Everything else — Submittals, ASI/CCD/ChangeOrder, FieldIssue, ClashItem,
Transmittal, ScheduleActivity, ModelObject, webhook dispatch, rate limiting —
is **not built yet**. See §7 below for the precise boundary.

---

## 2. Prerequisites

- Docker Desktop running.
- Run every command from the **repo root** (`C:\Users\ankit\Downstream`).

**Known local fix already applied:** `infra/docker-compose.yml`'s
`reference-engineering-backend` and `reference-engineering-frontend` build
paths were changed from `./reference-systems/...` to `../reference-systems/...`
(this is currently an *uncommitted* local change — check `git status`). This
is required because Compose resolves build paths relative to the compose
file's own directory (`infra/`), not the repo root. Without it, the build
fails. If that diff is ever reverted, either re-apply it or run every command
below with `--project-directory .` added after `-f infra/docker-compose.yml`.

---

## 3. Starting the stack

```bash
docker compose -f infra/docker-compose.yml up --build reference-engineering-db reference-engineering-backend reference-engineering-frontend
```

Add `-d` to run detached. This starts three containers:

| Service | Port | What it is |
|---|---|---|
| `reference-engineering-db` | 5432 (internal only) | PostgreSQL 16 |
| `reference-engineering-backend` | `localhost:8000` | FastAPI |
| `reference-engineering-frontend` | `localhost:3100` | Next.js |

Check they're up:

```bash
docker compose -f infra/docker-compose.yml ps
```

---

## 4. First-time setup — migrations + seed data

**This step does not run automatically.** The backend container's only
startup command is `uvicorn` — nothing runs Alembic or seeds the database on
its own. On a fresh database (or after `docker compose down -v`), you must
run both of these once, in order:

```bash
docker compose -f infra/docker-compose.yml exec reference-engineering-backend python -m alembic upgrade head
docker compose -f infra/docker-compose.yml exec reference-engineering-backend python -m seed.run_seed
```

If you skip this, `/login` will 500 (the `users` table won't exist yet) or,
after migrations but before seeding, will 401 for every credential (no rows
exist).

**Expected seed output:**

```
Seed complete:
  project_id: 1
  rfi_id: 1
  drawing_id: 1
  current_version_id: 2
  ananya_user_id: 1
  demo_password: downstream-demo
```

Re-running `seed.run_seed` against an already-seeded database is not
something this guide verifies — if you need a clean slate, tear the volume
down and start over:

```bash
docker compose -f infra/docker-compose.yml down -v
docker compose -f infra/docker-compose.yml up --build -d reference-engineering-db reference-engineering-backend reference-engineering-frontend
# then repeat the two commands above
```

---

## 5. Logging in

Go to **http://localhost:3100/login**.

All seeded human users share one demo password: **`downstream-demo`**

| Email | Role |
|---|---|
| `ananya.rao@meridiangc.example` | PROJECT_MANAGER |
| `kabir.mehta@meridiangc.example` | PROJECT_ENGINEER |
| `rhea.fernandes@archstudio.example` | ARCHITECT_ENGINEER_OF_RECORD |
| `vikram.suresh@arjunsteelworks.example` | SUBCONTRACTOR |
| `admin@downstream.example` | ADMIN |

Start with **Ananya Rao (PROJECT_MANAGER)** — she's the primary actor in the
seeded Reference Trace scenario.

### Why every role sees the same thing

This is by design, not a bug, and not yet a limitation worth fixing. Human
logins all resolve to one `ActingContext(kind="human")`, and its
`can_see()` check (`backend/src/api/deps.py`) unconditionally returns `True`
for every human role. Role is stored and displayed (bottom-left of the
sidebar) but nothing in the API currently gates on it.

Role-based *restriction* only exists on the **other** auth surface — OAuth2
integration clients (what a connector uses), which are scoped by
`PermissionScope` (`full` vs. `partial`). That asymmetry is intentional:
`docs/04_Downstream_Connector_Layer_Validation.md` specifically calls out
partial-scope *integration* behavior (silently empty results, not a 403) as
the highest-value thing to get right — human role-gating was never in
RES-1's scope. It isn't in the source-of-truth reference doc either;
`docs/reference/The Reference Engineering System.md` explicitly states it
"deliberately excludes API, integration, authentication, and UI concerns."

---

## 6. What you can actually do right now (user journey)

1. **`/login`** — sign in as any user above.
2. **`/dashboard`** — open/closed RFI counts for your project, plus a recent
   RFI activity list.
3. **`/projects`** (Project Explorer) — lists every project the account can
   see. Right now that's exactly one: "Meridian Tower." Click through to its
   RFIs.
4. **`/projects/1/rfis`** (RFI Register) — table of RFIs on the project.
   Right now that's exactly one: RFI-214.
5. **`/projects/1/rfis/1`** (RFI Detail) — subject, question, response,
   ball-in-court, cost-impact flag, cited spec sections, cited drawing
   revisions (Rev B *superseded* → Rev C *current*, with its revision cloud
   description), cited locations. A "Close RFI" button would appear here
   **only if the RFI weren't already closed** — see the gap noted in §8.

There is no page and no API for creating or editing a Project, Drawing,
SpecSection, or Location. Read-only, full stop, for those five entities.

---

## 7. What is explicitly NOT implemented yet

Pulled directly from `IMPLEMENTATION_STATUS.md` §10.9 — this is tracked
scope, not an oversight:

- **No create endpoints anywhere** — not for RFIs, not for Drawings, not for
  Projects. The only RFI *write* actions that exist are
  `PATCH /rfis/{id}/respond` and `PATCH /rfis/{id}/close` — both assume the
  RFI already exists.
- **Webhook dispatch** on RFI close — not wired (RES-2).
- **Rate limiting / pagination** (`X-Total`, `per_page`) — not implemented
  (RES-2).
- **Submittals, Vendor/Commitment, procurement-gate enforcement** — not
  implemented (RES-3).
- **DesignChange (ASI/Bulletin/CCD/ChangeOrder), ChangeEvent/PCO/COR,
  FieldIssue, ClashItem, Transmittal** — not implemented (RES-4).
- **ScheduleActivity, ModelObject** — not implemented (RES-5).
- **Drawing Register/Detail/Revision Timeline, Submittal Register,
  Specification Browser, Location Hierarchy, Activity Feed pages** — backend
  groundwork exists for some (documents, spec_sections, locations); frontend
  pages are deferred to RES-2 through RES-4.
- **Playwright / browser e2e tests** — RES-5.
- **Human role-based access control** — never scoped for RES-1; see §5.

---

## 8. Known gap: you cannot currently exercise the RFI write path

RFI-214 (the only RFI that exists) is seeded **already closed**, through its
real state machine, at the trace's literal timestamp. The frontend's "Close
RFI" button only renders when `status !== "CLOSED"`, so it won't appear for
it — and there's no create-RFI capability (UI or API) to make a fresh one to
test against.

If you want to see `respond`/`close` actually work, there are two options —
ask and I'll do either:

1. **One-off demo reset** — manually flip RFI-214 back to `OPEN` directly in
   the database, then call the two PATCH endpoints via `curl`/Postman to
   watch the transitions and re-fetch the RFI Detail page.
2. **Add a create-RFI endpoint** — a small, out-of-plan addition to
   `api/v1/rfis.py` + a matching frontend form, so you can seed your own test
   RFIs going forward. This wasn't in RES-1's approved scope, so it should be
   a deliberate decision, not something done silently.

---

## 9. Useful commands reference

```bash
# Status of the three containers
docker compose -f infra/docker-compose.yml ps

# Logs (add -f to follow)
docker compose -f infra/docker-compose.yml logs reference-engineering-backend

# Stop containers (keeps data)
docker compose -f infra/docker-compose.yml stop reference-engineering-db reference-engineering-backend reference-engineering-frontend

# Stop AND wipe the database volume (next start needs migrate + seed again)
docker compose -f infra/docker-compose.yml down -v

# Backend health check
curl http://localhost:8000/health

# Login via API directly (useful for testing without the browser)
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ananya.rao@meridiangc.example","password":"downstream-demo"}'

# Backend's own test suite (run on the host, not in the container —
# needs a Postgres reachable at RES_DATABASE_URL)
cd reference-systems/reference-engineering-system/backend
.venv/Scripts/python -m pytest -q
# expected: 20 passed
```

---

## 10. If something's wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| `/login` returns 500 | Migrations never ran | Run the `alembic upgrade head` command in §4 |
| `/login` returns 401 for every known credential | Seed never ran | Run the `seed.run_seed` command in §4 |
| `docker compose ... up --build` fails to find a build context | The `docker-compose.yml` path fix in §2 isn't applied | Check `git status` / re-apply the `../` build paths, or add `--project-directory .` |
| Changes you make don't seem to appear | You're rebuilding without `--build`, or looking at a stopped container's old image | `docker compose -f infra/docker-compose.yml up --build ...` again |
| Data disappeared after a restart | You ran `down -v` (wipes the volume) | Re-run migrate + seed (§4) — this is expected, not a bug |
