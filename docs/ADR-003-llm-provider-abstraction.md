# ADR-003: LLM provider abstraction

## Status

Accepted - 2026-09-09

## Decision

M4 defines a `RuleGenerator` protocol and provides `FakeRuleGenerator` as the default. It receives only a dataset profile and produces deterministic, untrusted structured candidate data. An optional future OpenAI-compatible adapter will be selected through environment configuration, not from application business logic.

## Consequences

Provider failures and malformed structured responses are tested deterministically. One service-layer Pydantic and semantic-validation path must reject bad candidates before persistence; no live model call is required in CI or in the basic demo flow.
