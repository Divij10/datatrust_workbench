import type { RuleRecord } from "../types";
import { StatusBadge } from "./StatusBadge";

interface RulesPanelProps {
  rules: RuleRecord[];
  requestingSuggestions: boolean;
  onSuggest: () => void;
  onUpdate: (ruleId: string, status: "approved" | "rejected") => void;
}

export function RulesPanel({ rules, requestingSuggestions, onSuggest, onUpdate }: RulesPanelProps) {
  return <section className="panel" aria-labelledby="rules-title"><div className="panel-heading panel-heading-actions"><div><p className="eyebrow">Human review</p><h2 id="rules-title">Quality rules</h2></div><button type="button" className="button-secondary" onClick={onSuggest} disabled={requestingSuggestions}>{requestingSuggestions ? "Requesting…" : "Request suggestions"}</button></div>{rules.length === 0 ? <p className="empty-copy">No rules yet. Request suggestions, then approve the checks you want to enforce.</p> : <div className="rule-list">{rules.map((record) => <article className="rule-row" key={record.id}><div className="rule-main"><div className="rule-title"><code>{record.rule.rule_type}</code> on <strong>{record.rule.column}</strong></div><p>{record.rule.description}</p><div className="badge-row"><StatusBadge value={record.source} /><StatusBadge value={record.status} /><StatusBadge value={record.rule.severity} /></div></div>{record.status === "proposed" && <div className="row-actions"><button type="button" className="button-quiet" onClick={() => onUpdate(record.id, "rejected")}>Reject</button><button type="button" onClick={() => onUpdate(record.id, "approved")}>Approve</button></div>}</article>)}</div>}</section>;
}
