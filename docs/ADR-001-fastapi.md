# ADR-001: FastAPI service boundary

## Status

Accepted - 2026-09-09

## Context

The workbench needs a typed HTTP API that remains easy to test while deterministic data-quality logic grows.

## Decision

Use FastAPI for transport, Pydantic v2 models for request and response boundaries, and keep profiling in a service class. Route handlers only read HTTP inputs, call a service, and return typed models. The first milestone uses an in-memory repository behind a small interface so later SQLite persistence does not change route or profiling code.

## Consequences

Tests can exercise profiling without HTTP and can exercise upload behavior through FastAPI's TestClient. Dataset records are intentionally temporary until the rule/audit domain needs durable persistence.
