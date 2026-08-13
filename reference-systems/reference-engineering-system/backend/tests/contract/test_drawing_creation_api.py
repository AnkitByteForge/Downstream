from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

# Drawing/DrawingVersion creation contract tests (E.4, ADR-009): the new
# POST .../documents and POST .../documents/{drawing_id}/versions routes,
# exercised against the full app -- real committed rows, real HTTP client.
# Covers successful creation, project isolation, scope enforcement,
# duplicate/idempotent-retry behavior, source_evidence_ref round-tripping,
# and regression coverage for the pre-existing GET/issue routes.


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Successful creation ------------------------------------------------


def test_create_drawing_succeeds_and_returns_201(drawing_creation_contract_fixture):
    client = TestClient(app)
    project_id = drawing_creation_contract_fixture["project_a"]
    resp = client.post(
        f"/rest/v1.0/projects/{project_id}/documents",
        json={"sheet_number": "E0.6", "title": "Electrical Panel Schedules", "discipline_code": "DC"},
        headers=_headers(drawing_creation_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["sheet_number"] == "E0.6"
    assert body["title"] == "Electrical Panel Schedules"
    assert body["project_id"] == project_id
    assert body["current_version_id"] is None


def test_create_drawing_version_succeeds_and_returns_201(drawing_creation_contract_fixture):
    client = TestClient(app)
    project_id = drawing_creation_contract_fixture["project_a"]
    drawing_id = drawing_creation_contract_fixture["existing_drawing_id"]
    resp = client.post(
        f"/rest/v1.0/projects/{project_id}/documents/{drawing_id}/versions",
        json={"revision_label": "Rev B", "discipline_code": "DC", "revision_clouds": []},
        headers=_headers(drawing_creation_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["revision_label"] == "Rev B"
    assert body["status"] == "DRAFT"
    assert body["drawing_id"] == drawing_id
    assert body["revision_clouds"] == []


# --- Invalid project / cross-project isolation ---------------------------


def test_create_drawing_for_a_different_project_than_the_credential_is_404(
    drawing_creation_contract_fixture,
):
    """The acting credential belongs to project B; posting against project
    A's path must not succeed -- same 404-hide posture every other route
    in this codebase already uses for tenancy mismatches."""
    client = TestClient(app)
    project_a = drawing_creation_contract_fixture["project_a"]
    resp = client.post(
        f"/rest/v1.0/projects/{project_a}/documents",
        json={"sheet_number": "E0.7", "title": "Should Not Be Created", "discipline_code": "DC"},
        headers=_headers(drawing_creation_contract_fixture["token_b_full"]),
    )
    assert resp.status_code == 404


def test_create_drawing_version_under_another_projects_drawing_is_404(
    drawing_creation_contract_fixture,
):
    """Project B's credential must not be able to create a version under
    project A's existing Drawing, even by guessing its id."""
    client = TestClient(app)
    project_b = drawing_creation_contract_fixture["project_b"]
    project_a_drawing_id = drawing_creation_contract_fixture["existing_drawing_id"]
    resp = client.post(
        f"/rest/v1.0/projects/{project_b}/documents/{project_a_drawing_id}/versions",
        json={"revision_label": "Rev X", "discipline_code": "DC", "revision_clouds": []},
        headers=_headers(drawing_creation_contract_fixture["token_b_full"]),
    )
    assert resp.status_code == 404


# --- Unauthorized client --------------------------------------------------


def test_create_drawing_with_no_token_is_401(drawing_creation_contract_fixture):
    client = TestClient(app)
    project_id = drawing_creation_contract_fixture["project_a"]
    resp = client.post(
        f"/rest/v1.0/projects/{project_id}/documents",
        json={"sheet_number": "E0.8", "title": "No Auth", "discipline_code": "DC"},
    )
    assert resp.status_code == 401


def test_create_drawing_with_out_of_scope_credential_is_404(drawing_creation_contract_fixture):
    """token_a_partial is scoped to "rfis" only, not "documents" -- the
    existing require_scope() 404-hide convention applies to creation too."""
    client = TestClient(app)
    project_id = drawing_creation_contract_fixture["project_a"]
    resp = client.post(
        f"/rest/v1.0/projects/{project_id}/documents",
        json={"sheet_number": "E0.9", "title": "Out of Scope", "discipline_code": "DC"},
        headers=_headers(drawing_creation_contract_fixture["token_a_partial"]),
    )
    assert resp.status_code == 404


# --- Duplicate creation / idempotent retry --------------------------------


def test_duplicate_drawing_creation_returns_the_existing_row_not_a_new_one(
    drawing_creation_contract_fixture,
):
    client = TestClient(app)
    project_id = drawing_creation_contract_fixture["project_a"]
    payload = {"sheet_number": "E0.10", "title": "Duplicate Test Sheet", "discipline_code": "DC"}
    headers = _headers(drawing_creation_contract_fixture["token_a_full"])

    first = client.post(f"/rest/v1.0/projects/{project_id}/documents", json=payload, headers=headers)
    second = client.post(f"/rest/v1.0/projects/{project_id}/documents", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_idempotent_retry_of_drawing_version_creation_never_duplicates(
    drawing_creation_contract_fixture,
):
    """The exact scenario named in the milestone spec: run #1 creates the
    version, a caller retries (simulating a network failure after RES
    committed) -- run #2 must return the SAME version, not a second one."""
    client = TestClient(app)
    project_id = drawing_creation_contract_fixture["project_a"]
    drawing_id = drawing_creation_contract_fixture["existing_drawing_id"]
    payload = {"revision_label": "Rev C", "discipline_code": "DC", "revision_clouds": []}
    headers = _headers(drawing_creation_contract_fixture["token_a_full"])

    run_1 = client.post(
        f"/rest/v1.0/projects/{project_id}/documents/{drawing_id}/versions", json=payload, headers=headers
    )
    run_2 = client.post(
        f"/rest/v1.0/projects/{project_id}/documents/{drawing_id}/versions", json=payload, headers=headers
    )
    run_3 = client.post(
        f"/rest/v1.0/projects/{project_id}/documents/{drawing_id}/versions", json=payload, headers=headers
    )

    assert run_1.status_code == 201
    assert run_2.status_code == 200
    assert run_3.status_code == 200
    assert run_1.json()["id"] == run_2.json()["id"] == run_3.json()["id"]

    listed = client.get(
        f"/rest/v1.0/projects/{project_id}/documents/{drawing_id}/versions", headers=headers
    )
    matching = [v for v in listed.json() if v["revision_label"] == "Rev C"]
    assert len(matching) == 1


# --- source_evidence_ref round trip ---------------------------------------


def test_source_evidence_ref_round_trips_through_the_creation_and_get_apis(
    drawing_creation_contract_fixture,
):
    client = TestClient(app)
    project_id = drawing_creation_contract_fixture["project_a"]
    drawing_id = drawing_creation_contract_fixture["existing_drawing_id"]
    headers = _headers(drawing_creation_contract_fixture["token_a_full"])
    evidence_ref = "dip://document/deadbeef/page/373/field/fed_from_panel?row=AH-9A"

    created = client.post(
        f"/rest/v1.0/projects/{project_id}/documents/{drawing_id}/versions",
        json={
            "revision_label": "Rev D",
            "discipline_code": "DC",
            "revision_clouds": [
                {
                    "area": "New Unit block, row AH-9A",
                    "delta_number": 1,
                    "description": "fed_from_panel = MR4",
                    "source_evidence_ref": evidence_ref,
                }
            ],
        },
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["revision_clouds"][0]["source_evidence_ref"] == evidence_ref

    fetched = client.get(
        f"/rest/v1.0/projects/{project_id}/documents/versions/{created.json()['id']}",
        headers=headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["revision_clouds"][0]["source_evidence_ref"] == evidence_ref


# --- Existing resource regressions -----------------------------------------


def test_existing_get_document_route_is_unaffected(drawing_creation_contract_fixture):
    client = TestClient(app)
    project_id = drawing_creation_contract_fixture["project_a"]
    drawing_id = drawing_creation_contract_fixture["existing_drawing_id"]
    resp = client.get(
        f"/rest/v1.0/projects/{project_id}/documents/{drawing_id}",
        headers=_headers(drawing_creation_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 200
    assert resp.json()["sheet_number"] == "E0.4"


def test_existing_list_document_versions_route_is_unaffected(drawing_creation_contract_fixture):
    client = TestClient(app)
    project_id = drawing_creation_contract_fixture["project_a"]
    drawing_id = drawing_creation_contract_fixture["existing_drawing_id"]
    resp = client.get(
        f"/rest/v1.0/projects/{project_id}/documents/{drawing_id}/versions",
        headers=_headers(drawing_creation_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 200
    labels = [v["revision_label"] for v in resp.json()]
    assert "Rev A" in labels


def test_existing_issue_transition_still_works_on_a_created_draft_version(
    drawing_creation_contract_fixture,
):
    """Proves E.4's new creation route composes cleanly with RES-4B's
    unmodified issuance endpoint -- create in DRAFT, then issue, exactly
    the two-step promotion flow the approved plan specifies."""
    client = TestClient(app)
    project_id = drawing_creation_contract_fixture["project_a"]
    drawing_id = drawing_creation_contract_fixture["existing_drawing_id"]
    headers = _headers(drawing_creation_contract_fixture["token_a_full"])

    created = client.post(
        f"/rest/v1.0/projects/{project_id}/documents/{drawing_id}/versions",
        json={"revision_label": "Rev E", "discipline_code": "DC", "revision_clouds": []},
        headers=headers,
    )
    assert created.status_code == 201
    version_id = created.json()["id"]

    issued = client.patch(
        f"/rest/v1.0/projects/{project_id}/documents/versions/{version_id}/issue",
        headers=headers,
    )
    assert issued.status_code == 200
    assert issued.json()["status"] == "ISSUED"
