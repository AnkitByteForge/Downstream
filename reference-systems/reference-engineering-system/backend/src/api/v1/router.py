from __future__ import annotations

from fastapi import APIRouter

from api.v1 import auth, documents, locations, oauth, projects, rfis, spec_sections

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(oauth.router)
api_router.include_router(projects.router, prefix="/rest/v1.0")
api_router.include_router(locations.router, prefix="/rest/v1.0")
api_router.include_router(spec_sections.router, prefix="/rest/v1.0")
api_router.include_router(documents.router, prefix="/rest/v1.0")
api_router.include_router(rfis.router, prefix="/rest/v1.0")
