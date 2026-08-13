from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import ActingContext, get_acting_context, get_login_user
from api.schemas.auth import LoginIn, SessionOut
from application.exceptions import InvalidCredentials
from application.use_cases.auth_use_cases import LoginUser
from infrastructure.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_COOKIE_NAME = "cs_session"


@router.post("/login")
def login(body: LoginIn, response: Response, use_case: LoginUser = Depends(get_login_user)) -> dict:
    try:
        token = use_case.execute(body.email, body.password)
    except InvalidCredentials as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
    )
    return {"status": "ok"}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"status": "ok"}


@router.get("/session", response_model=SessionOut)
def get_session(ctx: ActingContext = Depends(get_acting_context)) -> SessionOut:
    if ctx.kind != "human":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not a human session")
    return SessionOut(user_id=ctx.user_id, role=ctx.role)
