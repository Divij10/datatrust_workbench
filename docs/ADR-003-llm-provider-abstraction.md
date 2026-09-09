# ADR-003: LLM provider abstraction

## Status

Accepted - 2026-09-09

## Decision

The later AI milestone will define a `RuleGenerator` protocol and offer a fake implementation as its default. An optional OpenAI-compatible adapter will be selected through environment configuration, not from application business logic.

## Consequences

Provider failures and malformed structured responses can be tested deterministically. No live model call is required in CI or in the basic demo flow.
