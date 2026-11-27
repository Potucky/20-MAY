"""Error paths on /posts. Status codes are the ones this public API actually returns."""

from __future__ import annotations

import pytest

from api_client.assertions import expect_json, expect_status

pytestmark = pytest.mark.negative


@pytest.mark.parametrize("post_id", [0, -1, 101, 9999, "abc"])
def test_unknown_post_is_404(posts, sla_ms, post_id) -> None:
    body = expect_json(posts.get(post_id), 404, sla_ms)
    assert body == {}


def test_unknown_user_filter_is_an_empty_list(posts, sla_ms) -> None:
    body = expect_json(posts.list(userId=999999), 200, sla_ms)
    assert body == []


def test_empty_object_is_accepted_and_not_validated(posts, sla_ms) -> None:
    """The demo API does not require title, body, or userId. It returns only an id."""
    body = expect_json(posts.create({}), 201, sla_ms)
    assert body == {"id": 101}


def test_malformed_json_returns_500(api_client, sla_ms) -> None:
    """A production API should answer 400. JSONPlaceholder answers 500, and the test records that."""
    response = api_client.post(
        "/posts",
        data="not-json",
        headers={"Content-Type": "application/json"},
    )
    expect_status(response, 500, sla_ms)


def test_trace_is_not_allowed(api_client, sla_ms) -> None:
    response = api_client.request("TRACE", "/posts")
    expect_status(response, 405, sla_ms)
