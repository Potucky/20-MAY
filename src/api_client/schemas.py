"""Load JSON Schemas and validate response bodies against them."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from api_client.config import PROJECT_ROOT

DEFAULT_SCHEMA_DIR = PROJECT_ROOT / "schemas"
_FORMAT_CHECKER = FormatChecker()


class SchemaStore:
    def __init__(self, directory: Path = DEFAULT_SCHEMA_DIR) -> None:
        self.directory = directory
        self._cache: dict[str, dict[str, Any]] = {}

    def get(self, name: str) -> dict[str, Any]:
        if name not in self._cache:
            path = self.directory / f"{name}.json"
            if not path.is_file():
                raise FileNotFoundError(f"Schema not found: {path}")
            self._cache[name] = json.loads(path.read_text(encoding="utf-8"))
        return self._cache[name]


def list_of(
    item_schema: dict[str, Any],
    *,
    min_items: int = 0,
    max_items: int | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "array", "items": item_schema}
    if min_items:
        schema["minItems"] = min_items
    if max_items is not None:
        schema["maxItems"] = max_items
    return schema


def assert_json_schema(instance: Any, schema: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema, format_checker=_FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(instance), key=_error_path)
    if not errors:
        return
    raise ValidationError(_format_errors(errors))


def _error_path(error: ValidationError) -> tuple[Any, ...]:
    return tuple(error.absolute_path)


def _format_errors(errors: list[ValidationError]) -> str:
    lines = [f"{len(errors)} schema error(s):"]
    for error in errors[:8]:
        path = ".".join(str(part) for part in error.absolute_path) or "<root>"
        lines.append(f"- {path}: {error.message}")
    remaining = len(errors) - 8
    if remaining > 0:
        lines.append(f"- ... {remaining} more")
    return "\n".join(lines)
