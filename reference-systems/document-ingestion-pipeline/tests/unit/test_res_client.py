"""E.5 -- dip.promote.res_client, tested entirely against an injected fake
transport. No test in this file makes a real network call or requires a
live RES instance, per the explicit instruction."""

from __future__ import annotations

import pytest

from dip.promote.res_client import (
    ResAuthenticationError,
    ResClientConfig,
    ResConnectionError,
    ResHttpError,
    ResPromotionClient,
    ResTimeoutError,
    TransportResponse,
)


class FakeTransport:
    """Records every call; returns pre-programmed responses in order, or
    raises a pre-programmed exception, per URL."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.post_responses: dict[str, list] = {}
        self.get_responses: dict[str, list] = {}

    def queue_post(self, url: str, response) -> None:
        self.post_responses.setdefault(url, []).append(response)

    def post(self, url, *, data=None, json=None, headers=None, timeout=None):
        self.calls.append({"method": "POST", "url": url, "data": data, "json": json, "headers": headers})
        queued = self.post_responses[url].pop(0)
        if isinstance(queued, Exception):
            raise queued
        return queued

    def get(self, url, *, headers=None, timeout=None):
        self.calls.append({"method": "GET", "url": url, "headers": headers})
        queued = self.get_responses[url].pop(0)
        if isinstance(queued, Exception):
            raise queued
        return queued


class FakeConnectionError(Exception):
    pass


class FakeTimeoutError(Exception):
    pass


@pytest.fixture(autouse=True)
def patch_requests_exceptions(monkeypatch):
    """Points the client's exception-classification tuples at our fake
    exception types, so FakeTransport doesn't need a real `requests`
    dependency to simulate a connection failure."""
    import dip.promote.res_client as res_client_module

    monkeypatch.setattr(res_client_module, "_CONNECTION_EXCEPTIONS", (FakeConnectionError,))
    monkeypatch.setattr(res_client_module, "_TIMEOUT_EXCEPTIONS", (FakeTimeoutError,))


def _config(base_url="http://res.test") -> ResClientConfig:
    return ResClientConfig(base_url=base_url, client_id="dip-client", client_secret="dip-secret")


def _token_response(expires_in=3600, access_token="tok-1") -> TransportResponse:
    return TransportResponse(
        status_code=200, json_body={"access_token": access_token, "refresh_token": "r", "expires_in": expires_in}
    )


class TestConfigFromEnv:
    def test_reads_all_fields_from_environment(self, monkeypatch):
        monkeypatch.setenv("DIP_RES_BASE_URL", "http://res.example/")
        monkeypatch.setenv("DIP_RES_CLIENT_ID", "cid")
        monkeypatch.setenv("DIP_RES_CLIENT_SECRET", "csecret")
        monkeypatch.setenv("DIP_RES_TIMEOUT_SECONDS", "5")

        config = ResClientConfig.from_env()

        assert config.base_url == "http://res.example"  # trailing slash stripped
        assert config.client_id == "cid"
        assert config.client_secret == "csecret"
        assert config.timeout_seconds == 5.0

    def test_missing_required_variable_raises_a_clear_error(self, monkeypatch):
        monkeypatch.delenv("DIP_RES_BASE_URL", raising=False)
        monkeypatch.delenv("DIP_RES_CLIENT_ID", raising=False)
        monkeypatch.delenv("DIP_RES_CLIENT_SECRET", raising=False)

        with pytest.raises(Exception, match="DIP_RES_BASE_URL"):
            ResClientConfig.from_env()

    def test_repr_never_includes_the_secret(self):
        config = _config()
        assert "dip-secret" not in repr(config)
        assert "redacted" in repr(config)


class TestTokenAcquisitionAndReuse:
    def test_first_call_acquires_a_token(self):
        transport = FakeTransport()
        transport.queue_post("http://res.test/oauth/token", _token_response())
        transport.queue_post(
            "http://res.test/rest/v1.0/projects/1/documents",
            TransportResponse(status_code=201, json_body={"id": 1, "sheet_number": "E0.4"}),
        )
        client = ResPromotionClient(_config(), transport=transport)

        client.create_drawing(1, "E0.4", "Air Handler Schedule", "E")

        token_calls = [c for c in transport.calls if c["url"].endswith("/oauth/token")]
        assert len(token_calls) == 1
        assert token_calls[0]["data"]["grant_type"] == "client_credentials"
        assert token_calls[0]["data"]["client_id"] == "dip-client"
        assert token_calls[0]["data"]["client_secret"] == "dip-secret"

    def test_token_is_reused_across_multiple_calls(self):
        transport = FakeTransport()
        transport.queue_post("http://res.test/oauth/token", _token_response())
        transport.queue_post(
            "http://res.test/rest/v1.0/projects/1/documents",
            TransportResponse(status_code=201, json_body={"id": 1}),
        )
        transport.queue_post(
            "http://res.test/rest/v1.0/projects/1/documents",
            TransportResponse(status_code=200, json_body={"id": 1}),
        )
        client = ResPromotionClient(_config(), transport=transport)

        client.create_drawing(1, "E0.4", "Sheet", "E")
        client.create_drawing(1, "E0.4", "Sheet", "E")

        token_calls = [c for c in transport.calls if c["url"].endswith("/oauth/token")]
        assert len(token_calls) == 1  # NOT re-acquired on the second call

    def test_token_is_refreshed_once_expired(self):
        clock_value = [1000.0]
        transport = FakeTransport()
        transport.queue_post("http://res.test/oauth/token", _token_response(expires_in=60, access_token="tok-1"))
        transport.queue_post(
            "http://res.test/rest/v1.0/projects/1/documents",
            TransportResponse(status_code=201, json_body={"id": 1}),
        )
        transport.queue_post("http://res.test/oauth/token", _token_response(expires_in=60, access_token="tok-2"))
        transport.queue_post(
            "http://res.test/rest/v1.0/projects/1/documents",
            TransportResponse(status_code=200, json_body={"id": 1}),
        )
        client = ResPromotionClient(_config(), transport=transport, clock=lambda: clock_value[0])

        client.create_drawing(1, "E0.4", "Sheet", "E")
        clock_value[0] += 120  # well past expiry (60s) + safety margin (30s)
        client.create_drawing(1, "E0.4", "Sheet", "E")

        token_calls = [c for c in transport.calls if c["url"].endswith("/oauth/token")]
        assert len(token_calls) == 2  # re-acquired after expiry

    def test_access_token_is_sent_as_a_bearer_header(self):
        transport = FakeTransport()
        transport.queue_post("http://res.test/oauth/token", _token_response(access_token="secret-tok"))
        transport.queue_post(
            "http://res.test/rest/v1.0/projects/1/documents",
            TransportResponse(status_code=201, json_body={"id": 1}),
        )
        client = ResPromotionClient(_config(), transport=transport)

        client.create_drawing(1, "E0.4", "Sheet", "E")

        create_call = next(c for c in transport.calls if c["url"].endswith("/documents"))
        assert create_call["headers"]["Authorization"] == "Bearer secret-tok"


class TestAuthenticationFailure:
    def test_401_on_token_endpoint_raises_authentication_error_not_retryable(self):
        transport = FakeTransport()
        transport.queue_post(
            "http://res.test/oauth/token", TransportResponse(status_code=401, json_body={"detail": "bad creds"})
        )
        client = ResPromotionClient(_config(), transport=transport)

        with pytest.raises(ResAuthenticationError) as exc_info:
            client.create_drawing(1, "E0.4", "Sheet", "E")
        assert exc_info.value.retryable is False

    def test_authentication_error_message_never_contains_the_client_secret(self):
        transport = FakeTransport()
        transport.queue_post(
            "http://res.test/oauth/token", TransportResponse(status_code=401, json_body={"detail": "bad creds"})
        )
        client = ResPromotionClient(_config(), transport=transport)

        with pytest.raises(ResAuthenticationError) as exc_info:
            client.create_drawing(1, "E0.4", "Sheet", "E")
        assert "dip-secret" not in str(exc_info.value)


class TestConnectionAndTimeoutErrors:
    def test_connection_error_is_wrapped_and_marked_retryable(self):
        transport = FakeTransport()
        transport.queue_post("http://res.test/oauth/token", FakeConnectionError("refused"))
        client = ResPromotionClient(_config(), transport=transport)

        with pytest.raises(ResConnectionError) as exc_info:
            client.create_drawing(1, "E0.4", "Sheet", "E")
        assert exc_info.value.retryable is True

    def test_timeout_error_is_wrapped_and_marked_retryable(self):
        transport = FakeTransport()
        transport.queue_post("http://res.test/oauth/token", FakeTimeoutError("slow"))
        client = ResPromotionClient(_config(), transport=transport)

        with pytest.raises(ResTimeoutError) as exc_info:
            client.create_drawing(1, "E0.4", "Sheet", "E")
        assert exc_info.value.retryable is True


class TestHttpErrors:
    def test_4xx_on_create_is_marked_non_retryable(self):
        transport = FakeTransport()
        transport.queue_post("http://res.test/oauth/token", _token_response())
        transport.queue_post(
            "http://res.test/rest/v1.0/projects/1/documents",
            TransportResponse(status_code=400, json_body={"detail": "bad request"}),
        )
        client = ResPromotionClient(_config(), transport=transport)

        with pytest.raises(ResHttpError) as exc_info:
            client.create_drawing(1, "E0.4", "Sheet", "E")
        assert exc_info.value.status_code == 400
        assert exc_info.value.retryable is False

    def test_5xx_on_create_is_marked_retryable(self):
        transport = FakeTransport()
        transport.queue_post("http://res.test/oauth/token", _token_response())
        transport.queue_post(
            "http://res.test/rest/v1.0/projects/1/documents",
            TransportResponse(status_code=503, json_body={"detail": "unavailable"}),
        )
        client = ResPromotionClient(_config(), transport=transport)

        with pytest.raises(ResHttpError) as exc_info:
            client.create_drawing(1, "E0.4", "Sheet", "E")
        assert exc_info.value.status_code == 503
        assert exc_info.value.retryable is True


class TestCreateDrawingVersion:
    def test_sends_revision_clouds_with_source_evidence_ref(self):
        transport = FakeTransport()
        transport.queue_post("http://res.test/oauth/token", _token_response())
        transport.queue_post(
            "http://res.test/rest/v1.0/projects/1/documents/9/versions",
            TransportResponse(status_code=201, json_body={"id": 5, "revision_label": "Rev A"}),
        )
        client = ResPromotionClient(_config(), transport=transport)

        result = client.create_drawing_version(
            project_id=1,
            drawing_id=9,
            revision_label="Rev A",
            discipline_code="E",
            revision_clouds=[
                {
                    "area": "row AH-9A",
                    "delta_number": 1,
                    "description": "fed_from_panel = MR4",
                    "source_evidence_ref": "dip://document/deadbeef/page/373/field/fed_from_panel?row=AH-9A",
                }
            ],
        )

        assert result == {"id": 5, "revision_label": "Rev A"}
        create_call = next(c for c in transport.calls if c["url"].endswith("/versions"))
        assert create_call["json"]["revision_clouds"][0]["source_evidence_ref"] == (
            "dip://document/deadbeef/page/373/field/fed_from_panel?row=AH-9A"
        )

    def test_defaults_to_empty_revision_clouds(self):
        transport = FakeTransport()
        transport.queue_post("http://res.test/oauth/token", _token_response())
        transport.queue_post(
            "http://res.test/rest/v1.0/projects/1/documents/9/versions",
            TransportResponse(status_code=201, json_body={"id": 5}),
        )
        client = ResPromotionClient(_config(), transport=transport)

        client.create_drawing_version(1, 9, "Rev A", "E")

        create_call = next(c for c in transport.calls if c["url"].endswith("/versions"))
        assert create_call["json"]["revision_clouds"] == []


class TestNoSecretLeakage:
    def test_client_secret_never_appears_in_any_call_url(self):
        transport = FakeTransport()
        transport.queue_post("http://res.test/oauth/token", _token_response())
        transport.queue_post(
            "http://res.test/rest/v1.0/projects/1/documents",
            TransportResponse(status_code=201, json_body={"id": 1}),
        )
        client = ResPromotionClient(_config(), transport=transport)
        client.create_drawing(1, "E0.4", "Sheet", "E")

        for call in transport.calls:
            assert "dip-secret" not in call["url"]
