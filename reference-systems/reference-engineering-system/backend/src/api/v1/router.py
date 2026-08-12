from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import enforce_rate_limit
from api.v1 import (
    activity,
    auth,
    design_changes,
    documents,
    locations,
    model_objects,
    oauth,
    projects,
    rfis,
    schedule_activities,
    spec_divisions,
    spec_sections,
    submittal_requirements,
    submittals,
    vendors,
    webhook_subscriptions,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(oauth.router)

# Rate limiting (docs/04's per-client_id budget) applies to the whole
# Procore-realistic surface — every resource an integration client can call.
_rest = APIRouter(prefix="/rest/v1.0", dependencies=[Depends(enforce_rate_limit)])
_rest.include_router(projects.router)
_rest.include_router(locations.router)
_rest.include_router(spec_sections.router)
_rest.include_router(spec_divisions.router)
_rest.include_router(documents.router)
_rest.include_router(design_changes.router)
_rest.include_router(rfis.router)
_rest.include_router(submittals.router)
_rest.include_router(vendors.router)
_rest.include_router(submittal_requirements.router)
_rest.include_router(schedule_activities.router)
_rest.include_router(model_objects.router)
_rest.include_router(activity.router)
api_router.include_router(_rest)

# Admin/setup surface — this system's own concern, not something a real
# Procore integration would ever call, so kept outside /rest/v1.0 and outside
# the rate-limit budget (registering a webhook is a one-time setup action).
api_router.include_router(webhook_subscriptions.router)
