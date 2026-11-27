"""Outgoing payloads checked before they are sent.

JSONPlaceholder accepts almost any body. These models keep invalid data out of
the happy-path tests so a bad payload fails here, with a clear message.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewPost:
    title: str
    body: str
    user_id: int

    def __post_init__(self) -> None:
        _require_text("title", self.title)
        _require_text("body", self.body)
        if type(self.user_id) is not int or self.user_id < 1:
            raise ValueError("user_id must be a positive integer")

    def to_payload(self) -> dict[str, object]:
        return {"title": self.title, "body": self.body, "userId": self.user_id}


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
