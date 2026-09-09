import type { QualityDimension, QualityReport } from "../types";
import { StatusBadge } from "./StatusBadge";

const dimensionLabels: Record<string, string> = { completeness: "Completeness", validity: "Validity", uniqueness: "Uniqueness", consistency: "Consistency" };
function dimensionScore(dimension: QualityDimension): string { return dimension.score === null ? "N/A" : `${dimension.score.toFixed(1)}%`; }

export function ReportPanel({ report, onEvaluate, evaluating }: { report: QualityReport | null; onEvaluate: () => void; evaluating: boolean }) {
  const violations = report?.results.flatMap((result) => result.violations) ?? [];
  return <section className="panel" aria-labelledby="report-title"><div className="panel-heading panel-heading-actions"><div><p className="eyebrow">Deterministic evaluation</p><h2 id="report-title">Quality report</h2></div><button type="button" onClick={onEvaluate} disabled={evaluating}>{evaluating ? "Evaluating…" : "Run approved rules"}</button></div>{report === null ? <p className="empty-copy">Approve one or more rules, then run the deterministic evaluation to create a report.</p> : <><div className="dimension-grid" aria-label="Quality dimensions">{Object.entries(report.dimensions).map(([key, value]) => <div className="dimension" key={key}><span>{dimensionLabels[key]}</span><strong>{dimensionScore(value)}</strong><small>{value.checks_passing}/{value.checks_evaluated} checks passing</small></div>)}</div><div className="issue-list" aria-label="Detected issues">{violations.length === 0 ? <p className="empty-copy">No violations were detected in the approved checks.</p> : violations.map((violation) => <div className="issue-row" key={`${violation.rule_id}-${violation.row_index}`}><StatusBadge value={violation.severity} /><span>Row {violation.row_index + 1} · <strong>{violation.column}</strong> · {violation.message}</span></div>)}</div></>}</section>;
}
