"""Post contract: read the fixture, check writes echo, and do not treat them as stored."""

from __future__ import annotations

from collections import Counter

import pytest

from api_client.assertions import expect_json
from api_client.models import NewPost
from api_client.schemas import assert_json_schema, list_of

@pytest.mark.smoke
def test_get_post_by_id(posts, schemas, sla_ms) -> None:
    response = posts.get(1)
    body = expect_json(response, 200, sla_ms)
    assert_json_schema(body, schemas.get("post"))
    assert body["id"] == 1
    assert body["userId"] == 1
    assert body["title"]
    assert body["body"]
    assert "x-ratelimit-limit" in response.headers


@pytest.mark.regression
def test_post_collection_shape(posts, schemas, sla_ms) -> None:
    body = expect_json(posts.list(), 200, sla_ms)
    assert_json_schema(body, list_of(schemas.get("post"), min_items=100, max_items=100))
    assert [item["id"] for item in body] == list(range(1, 101))
    assert Counter(item["userId"] for item in body) == {user_id: 10 for user_id in range(1, 11)}
    assert all(item["title"].strip() and item["body"].strip() for item in body)


@pytest.mark.regression
def test_limit_and_page(posts, sla_ms) -> None:
    body = expect_json(posts.list(_page=2, _limit=10), 200, sla_ms)
    assert [item["id"] for item in body] == list(range(11, 21))


@pytest.mark.regression
def test_sort_descending(posts, sla_ms) -> None:
    body = expect_json(posts.list(_sort="id", _order="desc", _limit=5), 200, sla_ms)
    ids = [item["id"] for item in body]
    assert ids == sorted(ids, reverse=True)
    assert ids[0] == 100


@pytest.mark.regression
def test_filter_by_user(posts, sla_ms) -> None:
    body = expect_json(posts.list(userId=1), 200, sla_ms)
    assert [item["id"] for item in body] == list(range(1, 11))
    assert all(item["userId"] == 1 for item in body)


@pytest.mark.regression
def test_create_echoes_the_payload_and_assigns_101(posts, schemas, sla_ms) -> None:
    payload = NewPost(title="Portfolio check", body="Contract echo", user_id=7).to_payload()
    body = expect_json(posts.create(payload), 201, sla_ms)
    assert_json_schema(body, schemas.get("post"))
    assert body["title"] == payload["title"]
    assert body["body"] == payload["body"]
    assert body["userId"] == payload["userId"]
    assert body["id"] == 101


@pytest.mark.regression
def test_replace_post(posts, schemas, sla_ms) -> None:
    payload = {"id": 1, "title": "replaced", "body": "new body", "userId": 3}
    body = expect_json(posts.replace(1, payload), 200, sla_ms)
    assert body == payload
    assert_json_schema(body, schemas.get("post"))


@pytest.mark.regression
def test_patch_changes_title_only(posts, sla_ms) -> None:
    original = expect_json(posts.get(1), 200, sla_ms)
    patched = expect_json(posts.update(1, {"title": "patched title"}), 200, sla_ms)
    assert patched["title"] == "patched title"
    assert patched["body"] == original["body"]
    assert patched["userId"] == original["userId"]
    assert patched["id"] == original["id"]


@pytest.mark.regression
def test_delete_post_returns_an_empty_object(posts, sla_ms) -> None:
    body = expect_json(posts.delete(1), 200, sla_ms)
    assert body == {}


@pytest.mark.regression
def test_created_post_is_not_retrievable(posts, sla_ms) -> None:
    """Writes are echoed and then discarded. Post 101 is not part of the fixture."""
    created = expect_json(
        posts.create(NewPost(title="temp", body="temp body", user_id=1).to_payload()),
        201,
        sla_ms,
    )
    assert created["id"] == 101
    missing = expect_json(posts.get(created["id"]), 404, sla_ms)
    assert missing == {}
