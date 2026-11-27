"""HTTP client behavior without a network."""

from __future__ import annotations

from typing import Any

import pytest
import requests

from api_client.client import APIClient
from api_client.config import Settings

pytestmark = pytest.mark.unit


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "base_url": "https://example.test",
        "timeout_seconds": 3.5,
        "max_response_time_ms": 1000,
        "verify_ssl": True,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


class FakeElapsed:
    def total_seconds(self) -> float:
        return 0.012


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        body: str = '{"id": 1}',
        content_type: str = "application/json",
    ) -> None:
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self.url = "https://example.test/posts"
        self.text = body
        self.content = body.encode()
        self.elapsed = FakeElapsed()

    def json(self) -> Any:
        if self.text == "{":
            raise ValueError("bad json")
        return {"id": 1}


def test_get_builds_url_timeout_and_boolean_query() -> None:
    client = APIClient(make_settings())
    captured: dict[str, Any] = {}

    def _capture(method: str, url: str, **kwargs: Any) -> FakeResponse:
        captured["args"] = (method, url)
        captured["kwargs"] = kwargs
        return FakeResponse()

    client.session.request = _capture  # type: ignore[method-assign]
    response = client.get("/posts", params={"userId": 1, "completed": True})

    assert response.status_code == 200
    assert response.json() == {"id": 1}
    assert response.elapsed_ms == pytest.approx(12)
    assert captured["args"] == ("GET", "https://example.test/posts")
    assert captured["kwargs"]["timeout"] == 3.5
    assert captured["kwargs"]["verify"] is True
    assert captured["kwargs"]["params"] == {"userId": 1, "completed": "true"}


def test_false_query_value_is_lowercase() -> None:
    client = APIClient(make_settings())
    captured: dict[str, Any] = {}

    def _capture(method: str, url: str, **kwargs: Any) -> FakeResponse:
        captured["params"] = kwargs["params"]
        return FakeResponse()

    client.session.request = _capture  # type: ignore[method-assign]
    client.get("/todos", params={"completed": False})
    assert captured["params"]["completed"] == "false"


def test_relative_path_is_rejected() -> None:
    client = APIClient(make_settings())
    with pytest.raises(ValueError, match="path must start"):
        client.get("posts")


def test_json_and_raw_body_together_are_rejected() -> None:
    client = APIClient(make_settings())
    with pytest.raises(ValueError, match="not both"):
        client.request("POST", "/posts", json_body={"a": 1}, data="raw")


def test_empty_json_body_is_not_parsed() -> None:
    client = APIClient(make_settings())
    client.session.request = lambda *args, **kwargs: FakeResponse(body="")  # type: ignore[method-assign]
    response = client.get("/posts")
    with pytest.raises(ValueError, match="no JSON body"):
        response.json()


def test_non_json_response_has_no_json_body() -> None:
    client = APIClient(make_settings())
    client.session.request = lambda *args, **kwargs: FakeResponse(  # type: ignore[method-assign]
        body="nope", content_type="text/plain"
    )
    response = client.get("/posts")
    assert response.text == "nope"
    with pytest.raises(ValueError, match="no JSON body"):
        response.json()


def test_invalid_json_reports_the_url() -> None:
    client = APIClient(make_settings())
    client.session.request = lambda *args, **kwargs: FakeResponse(body="{")  # type: ignore[method-assign]
    response = client.get("/posts")
    with pytest.raises(ValueError, match="not valid JSON"):
        response.json()


def test_transport_errors_are_reraised() -> None:
    client = APIClient(make_settings())

    def _boom(*args: object, **kwargs: object) -> FakeResponse:
        raise requests.ConnectionError("boom")

    client.session.request = _boom  # type: ignore[method-assign]
    with pytest.raises(requests.ConnectionError):
        client.get("/posts")


def test_context_manager_closes_the_session() -> None:
    client = APIClient(make_settings())
    closed = {"value": False}
    client.session.close = lambda: closed.__setitem__("value", True)  # type: ignore[method-assign]
    with client:
        assert client.settings.base_url == "https://example.test"
    assert closed["value"] is True
