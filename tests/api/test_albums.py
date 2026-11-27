"""Albums: ten per user, and the nested user route agrees with the filter."""

from __future__ import annotations

from collections import Counter

import pytest

from api_client.assertions import expect_json
from api_client.schemas import assert_json_schema, list_of


@pytest.mark.regression
def test_album_collection_shape(albums, schemas, sla_ms) -> None:
    body = expect_json(albums.list(), 200, sla_ms)
    assert_json_schema(body, list_of(schemas.get("album"), min_items=100, max_items=100))
    assert [item["id"] for item in body] == list(range(1, 101))
    assert Counter(item["userId"] for item in body) == {user_id: 10 for user_id in range(1, 11)}


@pytest.mark.regression
def test_user_albums_match_the_filter(users, albums, schemas, sla_ms) -> None:
    nested = expect_json(users.albums(3), 200, sla_ms)
    filtered = expect_json(albums.list(userId=3), 200, sla_ms)
    assert nested == filtered
    assert_json_schema(nested, list_of(schemas.get("album"), min_items=10, max_items=10))
    assert all(item["userId"] == 3 for item in nested)
