"""Fixtures shared by the live API tests. Nothing here opens a connection by itself."""

from __future__ import annotations

from pathlib import Path

import pytest

from api_client.client import APIClient
from api_client.config import PROJECT_ROOT, load_settings
from api_client.resources import (
    AlbumsResource,
    CommentsResource,
    PostsResource,
    TodosResource,
    UsersResource,
)
from api_client.schemas import SchemaStore

REPORTS_DIR = PROJECT_ROOT / "reports"


def pytest_configure(config: pytest.Config) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)


@pytest.hookimpl(optionalhook=True)
def pytest_html_report_title(report: object) -> None:
    report.title = "JSONPlaceholder API tests"  # type: ignore[attr-defined]


@pytest.hookimpl(optionalhook=True)
def pytest_metadata(metadata: dict[str, object]) -> None:
    metadata["Project"] = "rest-api-testing-pytest"
    metadata["Target"] = "https://jsonplaceholder.typicode.com"
    for key in list(metadata):
        upper = key.upper()
        if any(secret in upper for secret in ("TOKEN", "SECRET", "PASSWORD", "KEY")):
            metadata.pop(key, None)


@pytest.fixture(scope="session")
def settings():
    return load_settings()


@pytest.fixture(scope="session")
def sla_ms(settings) -> int:
    return settings.max_response_time_ms


@pytest.fixture(scope="session")
def api_client(settings):
    client = APIClient(settings)
    yield client
    client.close()


@pytest.fixture(scope="session")
def posts(api_client) -> PostsResource:
    return PostsResource(api_client)


@pytest.fixture(scope="session")
def comments(api_client) -> CommentsResource:
    return CommentsResource(api_client)


@pytest.fixture(scope="session")
def users(api_client) -> UsersResource:
    return UsersResource(api_client)


@pytest.fixture(scope="session")
def todos(api_client) -> TodosResource:
    return TodosResource(api_client)


@pytest.fixture(scope="session")
def albums(api_client) -> AlbumsResource:
    return AlbumsResource(api_client)


@pytest.fixture(scope="session")
def schemas() -> SchemaStore:
    return SchemaStore(Path(__file__).resolve().parents[1] / "schemas")
