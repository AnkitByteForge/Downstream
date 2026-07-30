from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from application.exceptions import Unauthorized
from application.ports import SessionClaims, SessionTokenServicePort
from infrastructure.config import Settings


class JwtSessionTokenService(SessionTokenServicePort):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def issue(self, claims: SessionClaims) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(claims.user_id),
            "project_id": claims.project_id,
            "role": claims.role,
            "iat": now,
            "exp": now + timedelta(minutes=self._settings.jwt_expire_minutes),
        }
        return jwt.encode(payload, self._settings.jwt_secret, algorithm=self._settings.jwt_algorithm)

    def verify(self, token: str) -> SessionClaims:
        try:
            payload = jwt.decode(
                token, self._settings.jwt_secret, algorithms=[self._settings.jwt_algorithm]
            )
        except jwt.PyJWTError as exc:
            raise Unauthorized("Invalid or expired session token") from exc
        return SessionClaims(
            user_id=int(payload["sub"]),
            project_id=int(payload["project_id"]),
            role=payload["role"],
        )
