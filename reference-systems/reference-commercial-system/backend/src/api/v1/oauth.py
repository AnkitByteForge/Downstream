from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, status

from api.deps import get_issue_token_from_client_credentials, get_settings
from api.schemas.oauth import TokenOut
from application.exceptions import InvalidCredentials
from application.use_cases.oauth_use_cases import IssueTokenFromClientCredentials
from infrastructure.config import Settings

router = APIRouter(prefix="/oauth", tags=["oauth"])


@router.post("/token", response_model=TokenOut)
def issue_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    use_case: IssueTokenFromClientCredentials = Depends(get_issue_token_from_client_credentials),
    cfg: Settings = Depends(get_settings),
) -> TokenOut:
    # client_credentials only (docs/04: SAP/Oracle integration is service-
    # account, not user-delegated — no authorization_code, no refresh_token).
    if grant_type != "client_credentials":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported grant_type: {grant_type}")
    try:
        token = use_case.execute(client_id, client_secret)
    except InvalidCredentials as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    return TokenOut(
        access_token=token.access_token,
        expires_in=cfg.oauth_access_token_expire_minutes * 60,
    )
