"""Settings resolution: YAML, then .env, then the process environment."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from api_client.config import PROJECT_ROOT, load_settings

pytestmark = pytest.mark.unit

ENV_KEYS = (
    "API_BASE_URL",
    "API_TIMEOUT_SECONDS",
    "API_MAX_RESPONSE_TIME_MS",
    "API_VERIFY_SSL",
)


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def write_config(directory: Path, **overrides: object) -> Path:
    values: dict[str, object] = {
        "base_url": "https://yaml.example",
        "timeout_seconds": 4,
        "max_response_time_ms": 1500,
        "verify_ssl": True,
    }
    values.update(overrides)
    path = directory / "settings.yaml"
    path.write_text(yaml.safe_dump(values), encoding="utf-8")
    return path


def test_committed_defaults_target_the_public_api(clean_env: None) -> None:
    settings = load_settings(dotenv_path=PROJECT_ROOT / "missing.env")
    assert settings.base_url == "https://jsonplaceholder.typicode.com"
    assert settings.timeout_seconds == 10
    assert settings.max_response_time_ms == 5000
    assert settings.verify_ssl is True


def test_yaml_values_are_used_when_nothing_overrides_them(tmp_path: Path, clean_env: None) -> None:
    path = write_config(tmp_path)
    settings = load_settings(config_path=path, dotenv_path=tmp_path / "missing.env")
    assert settings.base_url == "https://yaml.example"
    assert settings.timeout_seconds == 4
    assert settings.max_response_time_ms == 1500
    assert settings.verify_ssl is True


def test_dotenv_overrides_yaml_and_env_overrides_dotenv(
    tmp_path: Path, clean_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_config(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "API_BASE_URL=https://dotenv.example\nAPI_TIMEOUT_SECONDS=8\nAPI_VERIFY_SSL=false\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("API_BASE_URL", "https://env.example/")
    settings = load_settings(config_path=path, dotenv_path=env_file)
    assert settings.base_url == "https://env.example"
    assert settings.timeout_seconds == 8
    assert settings.max_response_time_ms == 1500
    assert settings.verify_ssl is False


def test_numeric_strings_and_yes_are_accepted(tmp_path: Path, clean_env: None) -> None:
    path = write_config(tmp_path, timeout_seconds="2.5", max_response_time_ms="2500", verify_ssl="yes")
    settings = load_settings(config_path=path, dotenv_path=tmp_path / "missing.env")
    assert settings.timeout_seconds == 2.5
    assert settings.max_response_time_ms == 2500
    assert settings.verify_ssl is True


def test_empty_config_names_the_missing_value(tmp_path: Path, clean_env: None) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing base_url"):
        load_settings(config_path=path, dotenv_path=tmp_path / "missing.env")


def test_config_must_be_a_mapping(tmp_path: Path, clean_env: None) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text("- just-a-list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_settings(config_path=path, dotenv_path=tmp_path / "missing.env")


def test_missing_config_file_raises(tmp_path: Path, clean_env: None) -> None:
    with pytest.raises(FileNotFoundError):
        load_settings(config_path=tmp_path / "missing.yaml", dotenv_path=tmp_path / "missing.env")


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"base_url": "jsonplaceholder.typicode.com"}, "absolute"),
        ({"timeout_seconds": 0}, "timeout_seconds"),
        ({"timeout_seconds": "slow"}, "timeout_seconds"),
        ({"timeout_seconds": True}, "timeout_seconds"),
        ({"max_response_time_ms": 0}, "max_response_time_ms"),
        ({"max_response_time_ms": 1.5}, "max_response_time_ms"),
        ({"max_response_time_ms": True}, "max_response_time_ms"),
        ({"max_response_time_ms": "nope"}, "max_response_time_ms"),
        ({"verify_ssl": "maybe"}, "boolean"),
        ({"verify_ssl": 1}, "boolean"),
    ],
)
def test_rejects_invalid_values(tmp_path: Path, clean_env: None, overrides: dict, match: str) -> None:
    path = write_config(tmp_path, **overrides)
    with pytest.raises(ValueError, match=match):
        load_settings(config_path=path, dotenv_path=tmp_path / "missing.env")
