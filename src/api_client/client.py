"""Requests session with timeouts, idempotent retries, and a small response object."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from api_client.config import Settings

logger = logging.getLogger("api_client")

_IDEMPOTENT_METHODS = frozenset(["GET", "HEAD", "OPTIONS"])


class APIResponse:
    """Status, body, and timing for one completed HTTP call."""

    def __init__(self, method: str, response: requests.Response) -> None:
        self.method = method.upper()
        self.status_code = response.status_code
        self.url = response.url
        self.headers = response.headers
        self.text = response.text
        self.elapsed_ms = response.elapsed.total_seconds() * 1000
        self._json_body: Any = None
        self._json_error: Exception | None = None
        self._parsed = False
        self._maybe_parse_json(response)

    def json(self) -> Any:
        if self._json_error is not None:
            raise ValueError(
                f"Response from {self.method} {self.url} is not valid JSON"
            ) from self._json_error
        if not self._parsed:
            raise ValueError(f"Response from {self.method} {self.url} has no JSON body")
        return self._json_body

    def _maybe_parse_json(self, response: requests.Response) -> None:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type.lower():
            return
        if not response.content:
            return
        try:
            self._json_body = response.json()
        except ValueError as exc:
            self._json_error = exc
            return
        self._parsed = True


class APIClient:
    """Shared session for the suite. Retries cover connection failures on safe methods only."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "rest-api-testing-pytest/1.0",
            }
        )
        retry = Retry(
            total=2,
            connect=2,
            read=2,
            backoff_factor=0.2,
            allowed_methods=_IDEMPOTENT_METHODS,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def __enter__(self) -> APIClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self.session.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        data: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> APIResponse:
        if json_body is not None and data is not None:
            raise ValueError("Pass json_body or data, not both")
        url = _build_url(self.settings.base_url, path)
        query = _normalize_params(params)
        try:
            raw = self.session.request(
                method.upper(),
                url,
                params=query,
                json=json_body,
                data=data,
                headers=dict(headers) if headers else None,
                timeout=self.settings.timeout_seconds,
                verify=self.settings.verify_ssl,
            )
        except requests.RequestException:
            logger.error("%s %s failed before a response", method.upper(), url)
            raise
        wrapped = APIResponse(method, raw)
        logger.info(
            "%s %s -> %s in %.0fms",
            wrapped.method,
            wrapped.url,
            wrapped.status_code,
            wrapped.elapsed_ms,
        )
        return wrapped

    def get(self, path: str, *, params: Mapping[str, Any] | None = None) -> APIResponse:
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        json_body: Any = None,
        data: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> APIResponse:
        return self.request("POST", path, json_body=json_body, data=data, headers=headers)

    def put(self, path: str, *, json_body: Any) -> APIResponse:
        return self.request("PUT", path, json_body=json_body)

    def patch(self, path: str, *, json_body: Any) -> APIResponse:
        return self.request("PATCH", path, json_body=json_body)

    def delete(self, path: str) -> APIResponse:
        return self.request("DELETE", path)


def _build_url(base_url: str, path: str) -> str:
    if not path.startswith("/"):
        raise ValueError(f"path must start with '/', got {path!r}")
    return f"{base_url}{path}"


def _normalize_params(params: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not params:
        return None
    query: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, bool):
            # requests would otherwise encode True/False, which this API does not match.
            query[key] = "true" if value else "false"
        else:
            query[key] = value
    return query
