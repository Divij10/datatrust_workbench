# Architecture

```text
React + TypeScript workspace
        |
        | HTTP/JSON
        v
FastAPI routes -> DatasetService -> DatasetProfiler -> pandas
       |
       +-----------> RuleService -> RuleSemanticValidator
                                      |
                                      v
                             DeterministicRuleEngine
                                      |
                                      v
                         ReportService -> QualityScorer
       |
       +-----------> RuleGenerator protocol -> FakeRuleGenerator (default)
       ^|
       ||
MCP tools (mounted at /mcp; same service instances)
        |
        v
InMemoryDatasetRepository (development-only)
```

Routes handle HTTP only. `DatasetService` validates uploads and coordinates parsing, size/row limits, identifier generation, and storage. `DatasetProfiler` produces deterministic column and dataset summaries. `RuleService` enforces a proposed-to-approved human gate and `RuleSemanticValidator` rejects invalid columns, incompatible types, and duplicate equivalents before `DeterministicRuleEngine` evaluates a finite allow-listed rule vocabulary. `ReportService` stores a deterministic result and asks `QualityScorer` to calculate the documented N/A-aware portfolio metric. The `RuleGenerator` provider boundary returns untrusted structured data; the default `FakeRuleGenerator` uses only profile metadata and has no network dependency. The optional local MCP transport is mounted at `/mcp` and delegates to the same app-scoped services, so it does not create a second business-logic path. Durable persistence remains deliberately outside this increment.
