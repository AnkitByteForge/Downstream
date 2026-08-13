from __future__ import annotations

from fastapi import APIRouter

from api.v1 import auth, commitments, contracts, cost_codes, oauth, purchase_orders, vendors

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(oauth.router)

# The whole SAP/Oracle-realistic surface (docs/04) lives under /rest/v1 —
# no rate-limit dependency yet (CS-6 scope per the approved plan); CSRF
# ceremony (issue on GET, require on writes) is applied per-route in each
# router module, not uniformly here, because only mutating routes require it.
_rest = APIRouter(prefix="/rest/v1")
_rest.include_router(vendors.router)
_rest.include_router(cost_codes.router)
_rest.include_router(contracts.router)
_rest.include_router(commitments.router)
_rest.include_router(purchase_orders.router)
api_router.include_router(_rest)
