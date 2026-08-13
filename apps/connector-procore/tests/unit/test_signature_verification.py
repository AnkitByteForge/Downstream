"""Pure-logic unit test for HMAC webhook signature verification, matching
RES's own infrastructure/webhooks/signing.py algorithm exactly
(hmac-sha256 over the raw body, hex digest, 'sha256=' prefix) and its real
header name, X-Signature (not docs/05's illustrative X-Procore-Signature —
see module docstring in client/res_client.py for the recorded deviation)."""

from __future__ import annotations

import hashlib
import hmac
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from inbound.app import _verify_signature


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_accepted():
    secret = "seed-webhook-secret"
    body = b'{"resource_name": "rfis"}'
    assert _verify_signature(secret, body, _sign(secret, body)) is True


def test_wrong_secret_rejected():
    body = b'{"resource_name": "rfis"}'
    assert _verify_signature("seed-webhook-secret", body, _sign("wrong-secret", body)) is False


def test_tampered_body_rejected():
    secret = "seed-webhook-secret"
    original_body = b'{"resource_name": "rfis"}'
    signature = _sign(secret, original_body)
    tampered_body = b'{"resource_name": "pos"}'
    assert _verify_signature(secret, tampered_body, signature) is False


def test_missing_signature_rejected():
    assert _verify_signature("seed-webhook-secret", b"{}", None) is False
