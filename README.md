# TrustBuilder

Trust scores per claim and per outlet, with receipts. The planning docs call this product **Trust Engine**; it's the same product.

TrustBuilder is API-first. It ingests articles from the outlets it covers, splits them into discrete claims, checks each claim against primary sources (FOIA records included) and existing fact-checks, and keeps every verdict as a timestamped record. Customers query scores; they never submit URLs. The design, data model, API surface and roadmap are in [PLAN.md](PLAN.md).

> **Status: Phase 0 skeleton. Every score this API returns is fixture data.** Fixture data is invented for development, and each response that carries it is labeled: `meta.data_status: "fixture"` in the body and the `X-TrustBuilder-Data: fixture` header. Real verification isn't wired up yet.

## Quick start

Requires [uv](https://docs.astral.sh/uv/). uv installs the Python version pinned in `.python-version` (3.13).

```sh
uv sync
cp .env.example .env

# Generate an API key. Keep the key; put only its sha256 digest in .env.
uv run python -m trustbuilder.keys
#   key:    tb_test_...
#   sha256: 3f1c...
# then set TRUSTBUILDER_API_KEY_SHA256=<the sha256 line> in .env

uv run uvicorn trustbuilder.api.app:create_app --factory --reload
```

```sh
curl -s localhost:8000/v1/claims/clm_fixture_0001/score \
  -H "Authorization: Bearer tb_test_..."

curl -s localhost:8000/v1/outlets/out_fixture_01/trust-index \
  -H "Authorization: Bearer tb_test_..."
```

Interactive docs are at <http://localhost:8000/docs>, and the OpenAPI spec is at `/openapi.json`.

## API

| Endpoint | Auth | Returns |
|---|---|---|
| `GET /health` | none | Liveness, version, and whether the server is serving fixture data |
| `GET /v1/claims/{claim_id}/score` | API key | The claim's current verdict next to its original verdict: label, 0–100 score, band, confidence, evidence strength, receipts |
| `GET /v1/outlets/{outlet_id}/trust-index` | API key | The outlet's current Trust Index with interval, window and inputs; the previous index and the change; recent history for a sparkline |

Conventions (PLAN.md §5):

- Send keys as `Authorization: Bearer <key>`. Keys look like `tb_test_…` or `tb_live_…`.
- Successful responses are `{"data": …, "meta": {"data_status", "methodology_version", "generated_at", "request_id"}}`.
- Errors are `{"error": {"code", "message", "details", "request_id"}}`, with codes `unauthorized` (401), `not_found` (404), `method_not_allowed` (405), `invalid_request` (400) and `internal_error` (500).
- Insufficient evidence is an answer, not an error. It returns `200` with a null score and band `insufficient_evidence`.
- Every response carries `X-Request-ID`, which matches `request_id` in the body.

Bands follow the Brand Book. The thresholds are starting values that haven't been calibrated against real data yet:

| Band | Score |
|---|---|
| `verified` | 75–100 |
| `leaning_verified` | 60–74 |
| `mixed` | 40–59 |
| `leaning_faltering` | 25–39 |
| `faltering` | 0–24 |
| `insufficient_evidence` | no score |

## Configuration

Settings come only from environment variables (or a git-ignored `.env`). See [.env.example](.env.example).

| Variable | Default | Meaning |
|---|---|---|
| `TRUSTBUILDER_ENV` | `development` | `development`, `test` or `production`. In production the app refuses to start on fixture data. |
| `TRUSTBUILDER_API_KEY_SHA256` | empty | Comma-separated SHA-256 digests of accepted keys. If it's empty, every `/v1` request gets 401. |
| `TRUSTBUILDER_STORE` | `fixture` | Where scores come from. Only `fixture` exists until the Postgres store lands. |

`.env.example` also reserves names for later phases (database, object storage, Anthropic, Google Fact Check Tools, FOIA.gov, search). The code doesn't read them yet.

**Secrets:** never commit a key, token or `.env` file. The server stores only key digests, and a raw key placed in `TRUSTBUILDER_API_KEY_SHA256` is rejected at startup without being echoed to the log.

## Fixture data

The fixtures live in [src/trustbuilder/store/fixtures/](src/trustbuilder/store/fixtures/), and their README lists the scenarios. The store refuses to load any record that could pass for real data:

- IDs start with `clm_fixture_` or `out_fixture_`.
- Names, claim text and quotes start with `[FIXTURE]`.
- Every URL and domain is a reserved name (`.example`, `.invalid`, …), so no real outlet, agency or fact-checker is ever scored.

## Development

```sh
uv run pytest               # tests
uv run ruff check .         # lint
uv run ruff format .        # format
uv run mypy                 # strict type check of src/ and tests/
```

CI (`.github/workflows/ci.yml`) runs the same checks on pushes to `master` and on pull requests.

```
src/trustbuilder/
  api/          FastAPI app factory, routes, auth, error envelope, response schemas
  domain/       vocabularies (labels, claim types, ...), score bands, ID prefixes
  store/        ScoreStore interface, record models with their invariants, fixture store + data
  config.py     settings from the environment
  keys.py       API key generation and hashing (python -m trustbuilder.keys)
tests/
```

The API depends only on the `ScoreStore` interface (`store/base.py`). A Postgres store over the append-only tables replaces the fixture store after the Phase 0 foundations spike.

## Next

The Phase 0 spikes in [PLAN.md §6](PLAN.md): foundations (Postgres + pgvector, object storage, append-only migrations), the golden set, the extraction bake-off, span-anchored claim extraction, the Fact Check Tools match rate, the queue decision, and scoping for FOIA and reach data.
