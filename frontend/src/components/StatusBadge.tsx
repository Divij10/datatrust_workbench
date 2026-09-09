import type { RuleSource, RuleStatus, Severity } from "../types";

type BadgeValue = RuleStatus | RuleSource | Severity;

export function StatusBadge({ value }: { value: BadgeValue }) {
  return <span className={`status-badge status-${value}`}>{value}</span>;
}
