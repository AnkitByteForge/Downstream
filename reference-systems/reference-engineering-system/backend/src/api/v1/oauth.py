from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, status

from api.deps import (
    get_issue_token_from_client_credentials,
    get_issue_token_from_code,
    get_refresh_oauth_token,
)
from api.schemas.oauth import TokenOut
from application.exceptions import InvalidCredentials, Unauthorized
from application.use_cases.oauth_use_cases import (
    ACCESS_TOKEN_TTL,
    IssueTokenFromAuthorizationCode,
    IssueTokenFromClientCredentials,
    RefreshOAuthToken,
)

router = APIRouter(prefix="/oauth", tags=["oauth"])


@router.post("/token", response_model=TokenOut)
def issue_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    code: str | None = Form(default=None),
    refresh_token: str | None = Form(default=None),
    issue_use_case: IssueTokenFromAuthorizationCode = Depends(get_issue_token_from_code),
    refresh_use_case: RefreshOAuthToken = Depends(get_refresh_oauth_token),
    client_credentials_use_case: IssueTokenFromClientCredentials = Depends(
        get_issue_token_from_client_credentials
    ),
) -> TokenOut:
    try:
        if grant_type == "authorization_code":
            if code is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "code is required")
            token = issue_use_case.execute(client_id, client_secret, code)
        elif grant_type == "refresh_token":
            if refresh_token is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "refresh_token is required")
            token = refresh_use_case.execute(client_id, client_secret, refresh_token)
        elif grant_type == "client_credentials":
            # ADR-009: the headless, server-to-server grant DIP's promotion
            # client (E.5) uses -- no code, no prior refresh_token needed.
            token = client_credentials_use_case.execute(client_id, client_secret)
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported grant_type: {grant_type}")
    except InvalidCredentials as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    except Unauthorized as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return TokenOut(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        expires_in=int(ACCESS_TOKEN_TTL.total_seconds()),
    )
