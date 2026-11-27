"""Todos: boolean filter encoding, known rows, and a full-collection count check."""

from __future__ import annotations

from collections import Counter

import pytest

from api_client.assertions import expect_json
from api_client.schemas import assert_json_schema, list_of
from case_data import load_cases

FILTERS = load_cases("todo_filters.yaml")


@pytest.mark.smoke
def test_get_open_todo(todos, schemas, sla_ms) -> None:
    body = expect_json(todos.get(1), 200, sla_ms)
    assert_json_schema(body, schemas.get("todo"))
    assert body["completed"] is False
    assert body["userId"] == 1
    assert body["title"] == "delectus aut autem"


@pytest.mark.regression
@pytest.mark.parametrize(
    "expected",
    FILTERS,
    ids=[f"user-{row['user_id']}-completed-{str(row['completed']).lower()}" for row in FILTERS],
)
def test_todo_filter(todos, schemas, sla_ms, expected) -> None:
    body = expect_json(
        todos.list(userId=expected["user_id"], completed=expected["completed"]),
        200,
        sla_ms,
    )
    assert_json_schema(
        body,
        list_of(schemas.get("todo"), min_items=expected["count"], max_items=expected["count"]),
    )
    assert all(item["userId"] == expected["user_id"] for item in body)
    assert all(item["completed"] is expected["completed"] for item in body)
    known = next(item for item in body if item["id"] == expected["known_id"])
    assert known["title"] == expected["known_title"]


@pytest.mark.regression
def test_user_todos_match_the_filter(users, todos, sla_ms) -> None:
    nested = expect_json(users.todos(1), 200, sla_ms)
    filtered = expect_json(todos.list(userId=1), 200, sla_ms)
    assert nested == filtered
    assert len(nested) == 20


@pytest.mark.regression
def test_todo_collection_is_twenty_per_user(todos, schemas, sla_ms) -> None:
    body = expect_json(todos.list(), 200, sla_ms)
    assert_json_schema(body, list_of(schemas.get("todo"), min_items=200, max_items=200))
    assert [item["id"] for item in body] == list(range(1, 201))
    assert Counter(item["userId"] for item in body) == {user_id: 20 for user_id in range(1, 11)}
    assert {item["completed"] for item in body} == {True, False}
