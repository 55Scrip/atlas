"""Sprint 23 -- OpenFIGI adapter parsing logic, unit-level. Uses a
fake `post_json_fn` shaped exactly like the real endpoint's documented
response (verified live during this sprint's investigation, see
`openfigi_adapter.py`'s own module docstring) -- never a real network
call in tests."""
from __future__ import annotations

import pytest

from atlas.alpha.security_identity_evidence.openfigi_adapter import (
    OpenFigiProviderUnavailable,
    map_ticker,
)


def test_request_shape_matches_documented_api():
    captured = {}

    def fake_post(url, body, headers):
        captured["url"] = url
        captured["body"] = body
        captured["headers"] = headers
        return [{"data": [{"figi": "F1", "ticker": "MSFT", "name": "MICROSOFT CORP", "exchCode": "US"}]}]

    map_ticker("MSFT", post_json_fn=fake_post)
    assert captured["url"] == "https://api.openfigi.com/v3/mapping"
    assert captured["body"] == [{"idType": "TICKER", "idValue": "MSFT", "exchCode": "US"}]


def test_single_match_parsed():
    def fake_post(url, body, headers):
        return [
            {
                "data": [
                    {
                        "figi": "BBG000BPH459",
                        "ticker": "MSFT",
                        "name": "MICROSOFT CORP",
                        "exchCode": "US",
                        "securityType": "Common Stock",
                        "marketSector": "Equity",
                    }
                ]
            }
        ]

    result = map_ticker("MSFT", post_json_fn=fake_post)
    assert len(result.matches) == 1
    assert result.matches[0].figi == "BBG000BPH459"
    assert result.matches[0].name == "MICROSOFT CORP"


def test_no_match_warning_response_is_empty_not_an_error():
    def fake_post(url, body, headers):
        return [{"warning": "No identifier found."}]

    result = map_ticker("ZZZZZNOTREAL", post_json_fn=fake_post)
    assert result.matches == ()


def test_multiple_matches_parsed():
    def fake_post(url, body, headers):
        return [
            {
                "data": [
                    {"figi": "F1", "ticker": "BRK-A", "name": "BERKSHIRE HATHAWAY INC", "exchCode": "US"},
                    {"figi": "F2", "ticker": "BRK-A", "name": "BERKSHIRE HATHAWAY INC", "exchCode": "LN"},
                ]
            }
        ]

    result = map_ticker("BRK-A", post_json_fn=fake_post)
    assert len(result.matches) == 2


def test_http_error_raises_provider_unavailable():
    def fake_post(url, body, headers):
        raise OpenFigiProviderUnavailable("simulated 500")

    with pytest.raises(OpenFigiProviderUnavailable):
        map_ticker("MSFT", post_json_fn=fake_post)


def test_malformed_response_shape_raises_provider_unavailable():
    def fake_post(url, body, headers):
        return {"not": "a list"}

    with pytest.raises(OpenFigiProviderUnavailable):
        map_ticker("MSFT", post_json_fn=fake_post)


def test_optional_api_key_header_sent_when_env_var_set(monkeypatch):
    monkeypatch.setenv("ATLAS_OPENFIGI_API_KEY", "secret123")
    captured = {}

    def fake_post(url, body, headers):
        captured["headers"] = headers
        return [{"warning": "No identifier found."}]

    map_ticker("MSFT", post_json_fn=fake_post)
    assert captured["headers"]["X-OPENFIGI-APIKEY"] == "secret123"


def test_no_api_key_header_when_env_var_unset(monkeypatch):
    monkeypatch.delenv("ATLAS_OPENFIGI_API_KEY", raising=False)
    captured = {}

    def fake_post(url, body, headers):
        captured["headers"] = headers
        return [{"warning": "No identifier found."}]

    map_ticker("MSFT", post_json_fn=fake_post)
    assert "X-OPENFIGI-APIKEY" not in captured["headers"]
