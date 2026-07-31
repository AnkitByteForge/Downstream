from __future__ import annotations

from infrastructure.webhooks.signing import sign_payload


def test_sign_payload_is_deterministic_for_same_secret_and_body():
    body = b'{"a":1}'
    assert sign_payload("secret", body) == sign_payload("secret", body)


def test_sign_payload_differs_by_secret():
    body = b'{"a":1}'
    assert sign_payload("secret-a", body) != sign_payload("secret-b", body)


def test_sign_payload_has_sha256_prefix():
    assert sign_payload("secret", b"body").startswith("sha256=")
