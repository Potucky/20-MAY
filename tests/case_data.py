"""Load YAML cases checked into tests/data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_DATA_DIR = Path(__file__).resolve().parent / "data"


def load_cases(name: str) -> list[dict[str, Any]]:
    path = _DATA_DIR / name
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, list) or not loaded:
        raise ValueError(f"{path} must contain a non-empty list")
    return loaded
