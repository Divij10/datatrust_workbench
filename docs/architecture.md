# Architecture

```text
React + TypeScript shell
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
        v
InMemoryDatasetRepository (M1-M2 only)
```

Routes handle HTTP only. `DatasetService` validates uploads and coordinates parsing, size/row limits, identifier generation, and storage. `DatasetProfiler` produces deterministic column and dataset summaries. `RuleService` enforces a proposed-to-approved human gate and `RuleSemanticValidator` rejects invalid columns, incompatible types, and duplicate equivalents before `DeterministicRuleEngine` evaluates a finite allow-listed rule vocabulary. `ReportService` stores a deterministic result and asks `QualityScorer` to calculate the documented N/A-aware portfolio metric. AI adapters, durable persistence, and MCP remain deliberately outside M0-M3.
