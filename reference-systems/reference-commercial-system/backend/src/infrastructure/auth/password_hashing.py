from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from application.ports import PasswordHasherPort

_ALGO = "pbkdf2_sha256"
_ITERATIONS = 260_000


class Pbkdf2PasswordHasher(PasswordHasherPort):
    """Stdlib-only PBKDF2 hashing — avoids a native-extension dependency
    for what is a reference/demo system, not a production identity
    provider. Used for both human user passwords and OAuth2 client
    secrets."""

    def hash(self, plain_text: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", plain_text.encode(), salt, _ITERATIONS)
        return f"{_ALGO}${_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"

    def verify(self, plain_text: str, hashed: str) -> bool:
        try:
            algo, iterations_s, salt_b64, digest_b64 = hashed.split("$")
            if algo != _ALGO:
                return False
            iterations = int(iterations_s)
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(digest_b64)
        except (ValueError, TypeError):
            return False
        actual = hashlib.pbkdf2_hmac("sha256", plain_text.encode(), salt, iterations)
        return hmac.compare_digest(actual, expected)
