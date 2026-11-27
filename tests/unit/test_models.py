"""Client-side payload rules. These do not call the network."""

from __future__ import annotations

import pytest

from api_client.models import NewPost

pytestmark = pytest.mark.unit


def test_new_post_payload_uses_api_field_names() -> None:
    payload = NewPost(title="Hello", body="Body text", user_id=7).to_payload()
    assert payload == {"title": "Hello", "body": "Body text", "userId": 7}


def test_surrounding_space_is_kept() -> None:
    payload = NewPost(title="  Hello  ", body="Body", user_id=1).to_payload()
    assert payload["title"] == "  Hello  "


@pytest.mark.parametrize(
    ("title", "body", "user_id"),
    [
        ("", "Body", 1),
        ("   ", "Body", 1),
        ("Title", "", 1),
        ("Title", "Body", 0),
        ("Title", "Body", -3),
        ("Title", "Body", True),
    ],
)
def test_new_post_rejects_invalid_fields(title: str, body: str, user_id: object) -> None:
    with pytest.raises(ValueError):
        NewPost(title=title, body=body, user_id=user_id)  # type: ignore[arg-type]
