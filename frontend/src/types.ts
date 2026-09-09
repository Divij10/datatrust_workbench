export type InferredType = "boolean" | "integer" | "number" | "datetime" | "string" | "unknown";
export type RuleStatus = "proposed" | "approved" | "rejected" | "disabled";
export type RuleSource = "ai" | "human";
export type Severity = "info" | "warning" | "critical";

export interface ValueCount { value: string | number | boolean; count: number; }

export interface ColumnProfile {
  name: string;
  inferred_type: InferredType;
  null_count: number;
  null_rate: number;
  distinct_count: number;
  distinct_rate: number;
  is_unique: boolean;
  sample_values: Array<string | number | boolean>;
  min_value: number | null;
  max_value: number | null;
  mean: number | null;
  median: number | null;
  min_length: number | null;
  max_length: number | null;
  top_values: ValueCount[];
}

export interface DatasetProfile { row_count: number; column_count: number; duplicate_row_count: number; columns: ColumnProfile[]; }
export interface DatasetMetadata { id: string; filename: string; file_type: "csv" | "json"; size_bytes: number; created_at: string; row_count: number; column_count: number; }

export interface RuleDefinition {
  rule_type: string;
  column: string;
  severity: Severity;
  description: string;
  min_value?: number;
  max_value?: number;
  value?: number;
  values?: Array<string | number | boolean>;
  pattern_id?: string;
  min_length?: number;
  max_length?: number;
}

export interface RuleAuditEvent { occurred_at: string; from_status: RuleStatus | null; to_status: RuleStatus; source: RuleSource; rationale: string | null; }
export interface RuleRecord { id: string; dataset_id: string; status: RuleStatus; source: RuleSource; created_at: string; rule: RuleDefinition; audit_events: RuleAuditEvent[]; }
export interface QualityDimension { score: number | null; applicable: boolean; checks_evaluated: number; checks_passing: number; }
export interface RuleViolation { row_index: number; column: string; rule_id: string; rule_type: string; severity: Severity; observed_value: string | number | boolean | null; message: string; }
export interface RuleExecutionSummary { rule_id: string; rule_type: string; checked_count: number; violation_count: number; violations: RuleViolation[]; }

export interface QualityReport {
  id: string;
  dataset_id: string;
  created_at: string;
  evaluated_rule_count: number;
  total_violation_count: number;
  results: RuleExecutionSummary[];
  quality_score: number | null;
  dimensions: { completeness: QualityDimension; validity: QualityDimension; uniqueness: QualityDimension; consistency: QualityDimension; };
}

export interface ApiErrorPayload { error?: { message?: string }; }
