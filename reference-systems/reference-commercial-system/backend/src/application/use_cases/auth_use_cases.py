from __future__ import annotations

from domain.repositories.user_repository import UserRepository

from application.exceptions import InvalidCredentials
from application.ports import PasswordHasherPort, SessionClaims, SessionTokenServicePort


class LoginUser:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasherPort,
        session_token_service: SessionTokenServicePort,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._session_token_service = session_token_service

    def execute(self, email: str, password: str) -> str:
        user = self._user_repo.get_by_email(email)
        if user is None or not self._password_hasher.verify(password, user.password_hash):
            raise InvalidCredentials("Invalid email or password")
        claims = SessionClaims(user_id=user.id, role=user.role)
        return self._session_token_service.issue(claims)
