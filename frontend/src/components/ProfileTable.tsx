import type { DatasetProfile } from "../types";

function percentage(value: number): string { return `${(value * 100).toFixed(1)}%`; }

export function ProfileTable({ profile }: { profile: DatasetProfile }) {
  return <section className="panel" aria-labelledby="columns-title"><div className="panel-heading"><div><p className="eyebrow">Schema</p><h2 id="columns-title">Columns</h2></div><span className="subtle">{profile.duplicate_row_count} duplicate rows</span></div><div className="table-wrap"><table><thead><tr><th>Column</th><th>Type</th><th>Missing</th><th>Distinct</th><th>Sample values</th></tr></thead><tbody>{profile.columns.map((column) => <tr key={column.name}><th scope="row">{column.name}</th><td><code>{column.inferred_type}</code></td><td>{column.null_count} ({percentage(column.null_rate)})</td><td>{column.distinct_count} ({percentage(column.distinct_rate)})</td><td>{column.sample_values.map(String).join(", ") || "—"}</td></tr>)}</tbody></table></div></section>;
}
