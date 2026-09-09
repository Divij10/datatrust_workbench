import type { RuleRecord } from "../types";
import { StatusBadge } from "./StatusBadge";

export function AuditPanel({ rules }: { rules: RuleRecord[] }) {
  const events = rules.flatMap((record) => record.audit_events.map((event) => ({ ...event, rule: record })));
  return <section className="panel" aria-labelledby="audit-title"><div className="panel-heading"><div><p className="eyebrow">Traceability</p><h2 id="audit-title">Audit trail</h2></div></div>{events.length === 0 ? <p className="empty-copy">Rule decisions and their sources will be recorded here.</p> : <ol className="audit-list">{events.map((event, index) => <li key={`${event.rule.id}-${event.occurred_at}-${index}`}><div><strong>{event.rule.rule.column}</strong> · {event.rule.rule.rule_type}</div><div className="audit-detail"><StatusBadge value={event.source} /><span>{event.from_status ?? "new"} → {event.to_status}</span><time dateTime={event.occurred_at}>{new Date(event.occurred_at).toLocaleString()}</time></div></li>)}</ol>}</section>;
}
