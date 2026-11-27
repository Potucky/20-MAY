"""Comments: nested route, query filter, and referential counts against posts."""

from __future__ import annotations

from collections import Counter

import pytest

from api_client.assertions import expect_json
from api_client.schemas import assert_json_schema, list_of


@pytest.mark.smoke
def test_comments_for_first_post(comments, schemas, sla_ms) -> None:
    body = expect_json(comments.list(postId=1), 200, sla_ms)
    assert_json_schema(body, list_of(schemas.get("comment"), min_items=5, max_items=5))
    assert [item["id"] for item in body] == list(range(1, 6))
    assert all(item["postId"] == 1 for item in body)


@pytest.mark.regression
def test_nested_comments_match_the_query(posts, comments, sla_ms) -> None:
    nested = expect_json(posts.comments(1), 200, sla_ms)
    queried = expect_json(comments.list(postId=1), 200, sla_ms)
    assert nested == queried


@pytest.mark.regression
def test_every_post_has_five_unique_comments(comments, schemas, sla_ms) -> None:
    body = expect_json(comments.list(), 200, sla_ms)
    assert_json_schema(body, list_of(schemas.get("comment"), min_items=500, max_items=500))
    assert len({item["id"] for item in body}) == 500
    counts = Counter(item["postId"] for item in body)
    assert set(counts) == set(range(1, 101))
    assert set(counts.values()) == {5}
