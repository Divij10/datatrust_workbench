# Rule-suggestion evaluation set

`backend/tests/evals/rule_suggestion_cases.json` is a deterministic ten-case mini-suite for the rule-suggestion boundary. It intentionally evaluates categories of useful rules rather than claiming general model intelligence.

For each provider run, record:

- **Structured-output rate:** provider responses parse into the expected envelope.
- **Pydantic-valid rate:** parsed candidates satisfy the discriminated rule models.
- **Semantic-valid rate:** candidates reference real, compatible columns and do not duplicate a rule.
- **Duplicate rate:** candidate rules equivalent to an existing rule.
- **Useful-rule precision:** human-reviewed proportion judged useful for the fixture.

The fake provider is expected to be deterministic and to produce no malformed output. Malformed and timed-out provider fixtures are covered by integration tests, proving that neither can create or execute a rule.
