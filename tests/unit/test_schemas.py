"""Schema files are valid, and they reject the shapes we care about."""

from __future__ import annotations

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from api_client.schemas import SchemaStore, assert_json_schema, list_of

pytestmark = pytest.mark.unit

SCHEMA_NAMES = ("post", "comment", "user", "todo", "album")


@pytest.fixture(scope="module")
def schemas() -> SchemaStore:
    return SchemaStore()


def test_schema_files_are_valid_draft_2020(schemas: SchemaStore) -> None:
    for name in SCHEMA_NAMES:
        Draft202012Validator.check_schema(schemas.get(name))


def test_post_schema_accepts_a_complete_post(schemas: SchemaStore) -> None:
    assert_json_schema(
        {"userId": 1, "id": 1, "title": "Hello", "body": "Body"},
        schemas.get("post"),
    )


def test_post_schema_rejects_a_missing_title(schemas: SchemaStore) -> None:
    with pytest.raises(ValidationError, match="title"):
        assert_json_schema({"userId": 1, "id": 1, "body": "Body"}, schemas.get("post"))


def test_post_schema_rejects_an_extra_field(schemas: SchemaStore) -> None:
    with pytest.raises(ValidationError):
        assert_json_schema(
            {"userId": 1, "id": 1, "title": "Hello", "body": "Body", "extra": True},
            schemas.get("post"),
        )


def test_user_schema_rejects_a_bad_email(schemas: SchemaStore) -> None:
    user = {
        "id": 1,
        "name": "Ada",
        "username": "ada",
        "email": "not-an-email",
        "phone": "1",
        "website": "example.com",
        "address": {
            "street": "Main",
            "suite": "1",
            "city": "Town",
            "zipcode": "00000",
            "geo": {"lat": "1.0", "lng": "2.0"},
        },
        "company": {"name": "Co", "catchPhrase": "Phrase", "bs": "bs"},
    }
    with pytest.raises(ValidationError, match="email"):
        assert_json_schema(user, schemas.get("user"))


def test_missing_schema_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="Schema not found"):
        SchemaStore(tmp_path).get("post")


def test_list_of_omits_bounds_unless_requested() -> None:
    schema = list_of({"type": "string"})
    assert schema == {"type": "array", "items": {"type": "string"}}


def test_schema_error_summary_stops_after_eight() -> None:
    with pytest.raises(ValidationError, match=r"9 schema error\(s\)") as caught:
        assert_json_schema(["x"] * 9, {"type": "array", "items": {"type": "integer"}})
    message = str(caught.value)
    assert message.count("\n- ") == 9
    assert message.endswith("- ... 1 more")


def test_list_of_sets_size_bounds(schemas: SchemaStore) -> None:
    schema = list_of(schemas.get("album"), min_items=2, max_items=2)
    assert schema["minItems"] == 2
    assert schema["maxItems"] == 2
    assert schema["items"]["title"] == "Album"
