"""Load runtime settings from YAML, then .env, then the process environment."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

import yaml
from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"
DEFAULT_DOTENV_PATH = PROJECT_ROOT / ".env"

_ENV_KEYS = {
    "base_url": "API_BASE_URL",
    "timeout_seconds": "API_TIMEOUT_SECONDS",
    "max_response_time_ms": "API_MAX_RESPONSE_TIME_MS",
    "verify_ssl": "API_VERIFY_SSL",
}


@dataclass(frozen=True)
class Settings:
    base_url: str
    timeout_seconds: float
    max_response_time_ms: int
    verify_ssl: bool


def load_settings(
    config_path: Path | None = None,
    dotenv_path: Path | None = None,
) -> Settings:
    """Return settings. Process env overrides .env, which overrides the YAML file."""
    file_values = _read_yaml(config_path or DEFAULT_CONFIG_PATH)
    dotenv_values = _read_dotenv(dotenv_path)
    base_url = _as_base_url(_pick("base_url", file_values, dotenv_values))
    timeout_seconds = _as_timeout(_pick("timeout_seconds", file_values, dotenv_values))
    max_response_time_ms = _as_positive_int(
        _pick("max_response_time_ms", file_values, dotenv_values),
        name="max_response_time_ms",
    )
    verify_ssl = _as_bool(_pick("verify_ssl", file_values, dotenv_values))
    return Settings(
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        max_response_time_ms=max_response_time_ms,
        verify_ssl=verify_ssl,
    )


def _read_yaml(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file must be a mapping: {path}")
    return loaded


def _read_dotenv(dotenv_path: Path | None) -> Mapping[str, str | None]:
    path = DEFAULT_DOTENV_PATH if dotenv_path is None else dotenv_path
    if not path.is_file():
        return {}
    return dotenv_values(path)


def _pick(key: str, file_values: Mapping[str, Any], dotenv_values: Mapping[str, str | None]) -> Any:
    env_key = _ENV_KEYS[key]
    if env_key in os.environ:
        return os.environ[env_key]
    from_file = _dotenv_value(dotenv_values, env_key)
    if from_file is not None:
        return from_file
    if key not in file_values or file_values[key] in (None, ""):
        raise ValueError(f"Missing {key}. Set {env_key} or add {key} to the config file.")
    return file_values[key]


def _dotenv_value(values: Mapping[str, str | None], key: str) -> str | None:
    raw = values.get(key)
    if raw is None or str(raw).strip() == "":
        return None
    return str(raw)


def _as_base_url(value: Any) -> str:
    text = str(value).strip().rstrip("/")
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"base_url must be an absolute http(s) URL, got {value!r}")
    return text


def _as_timeout(value: Any) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"timeout_seconds must be a positive number, got {value!r}")
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"timeout_seconds must be a positive number, got {value!r}") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"timeout_seconds must be a positive number, got {value!r}")
    return number


def _as_positive_int(value: Any, *, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    if isinstance(value, int):
        number = value
    else:
        text = str(value).strip()
        try:
            parsed = float(text)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be a positive integer, got {value!r}") from exc
        if not parsed.is_integer():
            raise ValueError(f"{name} must be a positive integer, got {value!r}")
        number = int(parsed)
    if number <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    return number


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise ValueError(f"Cannot interpret boolean value: {value!r}")
