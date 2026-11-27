"""Shared checks for live responses. Messages include the URL, status, and timing."""

from __future__ import annotations

from typing import Any

from api_client.client import APIResponse


def expect_status(response: APIResponse, status: int, max_ms: int) -> APIResponse:
    assert response.status_code == status, (
        f"{response.method} {response.url} returned {response.status_code}, expected {status}. "
        f"Body starts: {response.text[:300]!r}"
    )
    assert response.elapsed_ms <= max_ms, (
        f"{response.method} {response.url} took {response.elapsed_ms:.0f} ms; limit is {max_ms} ms"
    )
    return response


def expect_json(response: APIResponse, status: int, max_ms: int) -> Any:
    expect_status(response, status, max_ms)
    content_type = response.headers.get("Content-Type", "")
    assert "application/json" in content_type.lower(), (
        f"{response.method} {response.url} content type is {content_type!r}, expected JSON"
    )
    return response.json()
