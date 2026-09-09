import type { QualityReport } from "../types";

function score(value: number | null | undefined): string { return value === null || value === undefined ? "—" : `${value.toFixed(1)}%`; }

export function MetricStrip({ report, rules }: { report: QualityReport | null; rules: number }) {
  const metrics = [
    { label: "Quality score", value: score(report?.quality_score), note: "Approved rules only" },
    { label: "Issues", value: report?.total_violation_count ?? "—", note: "Detected violations" },
    { label: "Rules", value: rules, note: "Configured checks" },
    { label: "Completeness", value: score(report?.dimensions.completeness.score), note: "Required checks" },
  ];
  return <section className="metric-strip" aria-label="Quality metrics">{metrics.map((metric) => <div className="metric" key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.note}</small></div>)}</section>;
}
