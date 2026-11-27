"""Users: schema, a checked reference set, and agreement with /posts?userId=."""

from __future__ import annotations

import pytest

from api_client.assertions import expect_json
from api_client.schemas import assert_json_schema, list_of
from case_data import load_cases

USERS = load_cases("users.yaml")


@pytest.mark.smoke
def test_get_first_user(users, schemas, sla_ms) -> None:
    body = expect_json(users.get(1), 200, sla_ms)
    assert_json_schema(body, schemas.get("user"))
    assert body["username"] == "Bret"
    assert body["address"]["city"] == "Gwenborough"
    # The public API sends coordinates as strings, not numbers.
    assert isinstance(body["address"]["geo"]["lat"], str)
    assert isinstance(body["address"]["geo"]["lng"], str)


@pytest.mark.regression
@pytest.mark.parametrize("expected", USERS, ids=[f"user-{row['id']}" for row in USERS])
def test_user_reference_row(users, schemas, sla_ms, expected) -> None:
    body = expect_json(users.get(expected["id"]), 200, sla_ms)
    assert_json_schema(body, schemas.get("user"))
    assert body["username"] == expected["username"]
    assert body["email"] == expected["email"]
    assert body["address"]["city"] == expected["city"]


@pytest.mark.regression
def test_user_directory_keys_are_unique(users, schemas, sla_ms) -> None:
    body = expect_json(users.list(), 200, sla_ms)
    assert_json_schema(body, list_of(schemas.get("user"), min_items=10, max_items=10))
    assert [item["id"] for item in body] == list(range(1, 11))
    assert len({item["username"] for item in body}) == 10
    assert len({item["email"].lower() for item in body}) == 10


@pytest.mark.regression
def test_user_posts_match_the_posts_filter(users, posts, sla_ms) -> None:
    nested = expect_json(users.posts(1), 200, sla_ms)
    filtered = expect_json(posts.list(userId=1), 200, sla_ms)
    assert nested == filtered
    assert [item["id"] for item in nested] == list(range(1, 11))
