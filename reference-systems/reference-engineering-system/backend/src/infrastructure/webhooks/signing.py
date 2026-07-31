from __future__ import annotations

import hashlib
import hmac


def sign_payload(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"
