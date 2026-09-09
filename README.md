# DataTrust Workbench

DataTrust Workbench is a local-first application for profiling tabular datasets, defining deterministic data-quality rules, and (in later milestones) reviewing AI-assisted rule suggestions. Its governing principle is: **AI may recommend; typed schemas and deterministic code validate; humans remain in control.**

It is an independent learning portfolio project exploring the data-integrity problem space. It is not affiliated with Precisely or any commercial data-quality product.

## Current scope

M0-M3 are implemented: a FastAPI/Pydantic v2 backend, a restrained React/TypeScript shell, CSV and JSON upload, bounded file and row limits, schema inference, deterministic profiling, typed data-quality rules, approval states, deterministic row-level execution, transparent quality scoring, and JSON reports. Live LLM support, persistent storage, and MCP are intentionally deferred to later milestones.

### Included

- `GET /health` liveness summary
- `POST /api/v1/datasets` for `.csv` and JSON-array-of-object uploads
- Dataset metadata and detailed profile endpoints
- Null, distinct, uniqueness, duplicate-row, numeric, string-length, and top-value summaries
- Typed required, unique, range, minimum, maximum, allowed-values, allow-listed pattern, email, and string-length rules
- Semantic validation for unknown columns, incompatible types, and duplicate equivalent rules
- Explicit proposed/approved/rejected/disabled lifecycle with an audit event for each transition
- Quality reports with row-level evidence, N/A-aware dimension metrics, and JSON export
- Consistent error envelope with request IDs
- Unit and API integration tests

### Explicit non-goals for this increment

- No generic chatbot or LLM call
- No automatic source-data modification
- No arbitrary code, SQL, or expression execution
- No authentication, cloud deployment, or MCP server

## Architecture

```text
React + TypeScript shell
        |
        v
FastAPI routes -> DatasetService -> DatasetProfiler -> pandas
       |               |
       |               v
       +-> RuleService -> semantic validator -> deterministic rule engine
                       |
                       v
            in-memory repository boundary (M1-M2)
```

Routes contain transport concerns only. Services validate and coordinate work; the profiler and rule engine remain deterministic. The M1-M2 repository is intentionally in-memory because durable records belong with the reporting/audit infrastructure in a later milestone. See [the fuller architecture note](docs/architecture.md).

## Quick start

Prerequisites: Python 3.12+, Node.js 22+, and Docker (for the one-command container workflow).

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:5173` for the shell and `http://localhost:8000/docs` for the API. The service uses no LLM key and no external model call in this scope.

For local development, create a virtual environment, install the backend extras, and install frontend packages:

```bash
cd backend && python -m pip install -e ".[dev]"
cd ../frontend && npm install
```

Run the API in one terminal with `make backend` and the web client in another with `make frontend`. Upload [messy_customers.csv](sample_data/messy_customers.csv) from the API docs or with `make demo`.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness and environment summary |
| POST | `/api/v1/datasets` | Upload CSV or JSON |
| GET | `/api/v1/datasets/{id}` | Dataset metadata |
| GET | `/api/v1/datasets/{id}/profile` | Deterministic profile |
| POST | `/api/v1/datasets/{id}/rules` | Create a proposed human-authored typed rule |
| GET | `/api/v1/datasets/{id}/rules` | List rules, optionally filtered by status/source |
| PATCH | `/api/v1/rules/{id}` | Approve, reject, or disable a rule |
| POST | `/api/v1/datasets/{id}/evaluate` | Execute approved rules and create a quality report |
| GET | `/api/v1/reports/{id}` | Fetch a deterministic quality report |
| GET | `/api/v1/reports/{id}/export` | Download the report as JSON |

Errors use a stable envelope such as:

```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "The uploaded file exceeds the configured size limit.",
    "details": {"max_size_bytes": 5242880},
    "request_id": "..."
  }
}
```

## Quality scoring and AI safety

The quality score is a transparent portfolio metric, not a universal industry standard. It weights completeness (35%), validity (30%), uniqueness (20%), and consistency (15%). Completeness comes from `required` checks; uniqueness from `unique`; consistency from `allowed_values`; and validity from the remaining format and range checks. A dimension with no values checked is shown as N/A (`null`) and its weight is re-normalized across applicable dimensions - it is never silently counted as perfect.

AI suggestions are also deferred. [ADR-002](docs/ADR-002-ai-validation-boundary.md) records the non-negotiable boundary: a future provider can suggest structured candidate rules, but Pydantic and semantic validation must accept them before human approval, and only the deterministic engine will execute approved rules.

## Checks

```bash
make test
make lint
make typecheck
cd frontend && npm run build
docker compose build
```

The GitHub Actions workflow runs these checks on pushes and pull requests. Later milestones will add fake and optional live LLM adapters, the browser workflow UI, SQLite persistence, and finally MCP tools that reuse the service layer.

## Why I built this

I built this to practice production-minded Python, Pydantic, testing, and responsible AI boundaries in a data-integrity domain: small enough to explain in an interview, structured enough to evolve without turning into an LLM wrapper.
