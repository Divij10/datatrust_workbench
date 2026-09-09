# ADR-004: Mount MCP tools in the existing FastAPI process

## Decision

Expose the optional MCP tools through a Streamable HTTP endpoint mounted at `/mcp` in the existing FastAPI process. The MCP server receives an explicit bundle of the same dataset, rule, and report services used by REST routes.

## Context

The MVP repository is intentionally in-memory. Running a separate stdio MCP process would create a separate repository and make dataset identifiers from the REST/browser workflow unusable by MCP tools.

## Consequences

MCP and REST operate on the same records while the app is running, and the MCP layer contains no duplicate profiling, rule, or reporting logic. The endpoint is local-only by default and has no authentication, so it is a development/portfolio capability rather than a hosted integration. A future durable repository and authentication model should precede remote MCP deployment.
