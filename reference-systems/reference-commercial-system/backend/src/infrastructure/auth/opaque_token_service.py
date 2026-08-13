from __future__ import annotations

import secrets

from application.ports import OpaqueTokenServicePort


class SecureOpaqueTokenService(OpaqueTokenServicePort):
    def generate(self) -> str:
        return secrets.token_urlsafe(32)
