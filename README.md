# REST API testing with pytest

[![API tests](https://github.com/Potucky/20-MAY/actions/workflows/api-tests.yml/badge.svg)](https://github.com/Potucky/20-MAY/actions/workflows/api-tests.yml)

Portfolio demo for QA Automation, SDET, and Data QA reviews. This is not employer code, and it does not test a private system. The live tests call the public [JSONPlaceholder](https://jsonplaceholder.typicode.com) API. That host needs no account and no credentials.

The badge reflects the default branch after this workflow is on it.

## What it demonstrates

- A client layer with a shared session, timeouts, and retries limited to safe HTTP methods
- Resource wrappers so tests do not build URLs themselves
- CRUD checks and negative checks against the published contract
- JSON Schema validation (Draft 2020-12), including nested objects and email format
- Data checks on the collections: counts, unique keys, and nested routes that must match filters
- Data-driven cases loaded from YAML
- Markers for a short smoke set, a broader regression set, negative cases, and offline unit tests
- A response-time budget on every live call, with no `sleep` in the tests
- GitHub Actions that runs the suite and uploads an HTML report, JUnit XML, and coverage XML

## Tech stack

| Piece | Choice |
| --- | --- |
| Language | Python 3.11+ (CI uses 3.12) |
| Runner | pytest |
| HTTP | requests |
| Contracts | jsonschema |
| Config | `config/settings.yaml`, optional `.env`, process environment |
| Reports | pytest-html (self-contained), JUnit XML, coverage XML |
| CI | GitHub Actions |

Pinned versions are in `requirements.txt`.

## Project structure

```text
config/settings.yaml          default base URL, timeout, response-time budget
src/api_client/               client, resources, payload model, schema helpers
schemas/                      Draft 2020-12 schemas for post, comment, user, todo, album
tests/api/                    live contract and data checks
tests/unit/                   no network
tests/data/                   reference rows for parametrized checks
.github/workflows/api-tests.yml
```

## Run locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

`pytest` writes:

- `reports/report.html` — self-contained HTML report
- `reports/junit.xml` — JUnit XML
- `reports/coverage.xml` — coverage of `src/api_client`

Useful subsets:

```bash
pytest -m unit        # offline
pytest -m smoke       # four critical-path calls
pytest -m regression
pytest -m negative
```

`make test`, `make unit`, `make smoke`, and `make negative` run the same commands.

## Configuration

Process environment wins over `.env`, which wins over `config/settings.yaml`. Copy `.env.example` to `.env` for local overrides. `.env` is gitignored. Do not put secrets in this repo; the demo API does not use any.

| Environment variable | YAML key | Default |
| --- | --- | --- |
| `API_BASE_URL` | `base_url` | `https://jsonplaceholder.typicode.com` |
| `API_TIMEOUT_SECONDS` | `timeout_seconds` | `10` |
| `API_MAX_RESPONSE_TIME_MS` | `max_response_time_ms` | `5000` |
| `API_VERIFY_SSL` | `verify_ssl` | `true` |

The timeout is the HTTP client limit. The response-time budget is a separate assertion, so a call that returns slowly still fails even when it is under the timeout. Local calls are usually tens of milliseconds. The 5000 ms budget is there so a slow network fails the test instead of making it flaky.

GET, HEAD, and OPTIONS retry up to two times on connection and read errors. POST, PUT, PATCH, and DELETE are not retried.

## CI

[`.github/workflows/api-tests.yml`](.github/workflows/api-tests.yml) runs on push and on pull request. It installs `requirements.txt`, runs `pytest`, and always uploads the `api-test-report` artifact with:

- `reports/report.html`
- `reports/junit.xml`
- `reports/coverage.xml`

The workflow sets the public base URL in the environment. It does not use repository secrets.

## Test approach

88 tests: 43 offline `unit`, 4 `smoke`, 32 `regression`, 9 `negative`. Each test has one of those markers.

| Marker | What it is for |
| --- | --- |
| `unit` | Config precedence, payload rules, schema failures, and the client with a fake transport |
| `smoke` | One post, one user, comments for post 1, one todo |
| `regression` | Collection shape, paging, sorting, filters, CRUD echo, cross-route agreement |
| `negative` | Unknown ids, an empty filter, and the error statuses this host actually returns |

Live checks share one helper. It asserts the status code, `Content-Type: application/json`, and the response-time budget, then returns the body. Schemas use `additionalProperties: false`, so a new field fails the build on purpose.

Data checks, in the same style as a small dataset review:

- 100 posts, ids `1..100`, 10 per user
- 500 comments, 5 per post, unique comment ids
- 10 users, unique usernames and emails, checked against `tests/data/users.yaml`
- 200 todos, 20 per user, plus known rows in `tests/data/todo_filters.yaml`
- 100 albums, 10 per user
- `/users/1/posts` matches `/posts?userId=1` (same idea for comments, albums, and todos)

Boolean filters are sent as `true` and `false`. The `requests` library would otherwise encode Python `True` / `False`, and JSONPlaceholder would not apply the filter.

Create requests on the happy path go through `NewPost`, which rejects a blank title, a blank body, and a non-positive `user_id` before anything is sent.

### What this suite does not claim

JSONPlaceholder is a fixed public fixture, not a system under our control.

- Writes are echoed and then discarded. `POST /posts` returns `201` and `"id": 101`. `GET /posts/101` is `404`. The suite asserts that, so a passing CRUD test does not mean the record was stored.
- An empty `POST` body is accepted and comes back as `{"id": 101}`. The host does not validate required fields. `NewPost` is the guard on our side.
- Malformed JSON is answered with `500`, not `400`. The negative test records that. A production API should reject it with `400`.
- `TRACE /posts` returns `405`.
- Coordinates on a user are strings (`"lat": "-37.3159"`), not numbers. The user schema locks the string type.
- `/photos` is about 5000 rows and is not requested. Nothing in the suite needs it.
- There is no authentication flow, because this API does not issue tokens.
- The counts above are the public fixture. They will fail if that fixture changes, which is the point of the check.

Coverage in the sample below is line and branch coverage of `src/api_client` only. It is not a coverage number for the third-party API.

## Sample output

Local run from the repository root:

```text
$ pytest
........................................................................ [ 81%]
................                                                         [100%]
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.3-final-0 ________________

Name                           Stmts   Miss Branch BrPart  Cover   Missing
--------------------------------------------------------------------------
src/api_client/__init__.py         1      0      0      0   100%
src/api_client/assertions.py      12      0      0      0   100%
src/api_client/client.py          91      0     18      0   100%
src/api_client/config.py          98      0     38      0   100%
src/api_client/models.py          17      0      4      0   100%
src/api_client/resources.py       38      0      0      0   100%
src/api_client/schemas.py         44      0     14      0   100%
--------------------------------------------------------------------------
TOTAL                            301      0     74      0   100%
Coverage XML written to file reports/coverage.xml
--------- Generated html report: file:///workspace/reports/report.html ---------
88 passed in 1.41s
```

One smoke call, with the client log:

```text
INFO api_client: GET https://jsonplaceholder.typicode.com/posts/1 -> 200 in 72ms
PASSED
```

Opening of `reports/junit.xml` from that run:

```xml
<testsuite name="pytest" errors="0" failures="0" skipped="0" tests="88" time="1.418">
  <testcase classname="tests.api.test_posts" name="test_get_post_by_id" time="0.016" />
</testsuite>
```

`reports/report.html` is a self-contained pytest-html report titled "JSONPlaceholder API tests". The environment block records the Python version, the project name, and the target URL. Open that file in a browser after a local run, or download the `api-test-report` artifact from a GitHub Actions run.
