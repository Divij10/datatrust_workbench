import { useRef, useState } from "react";

import { api } from "./api/client";
import { AuditPanel } from "./components/AuditPanel";
import { MetricStrip } from "./components/MetricStrip";
import { ProfileTable } from "./components/ProfileTable";
import { ReportPanel } from "./components/ReportPanel";
import { RulesPanel } from "./components/RulesPanel";
import type { DatasetMetadata, DatasetProfile, QualityReport, RuleRecord } from "./types";

type BusyAction = "upload" | "suggest" | "evaluate" | null;

export function App() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dataset, setDataset] = useState<DatasetMetadata | null>(null);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [rules, setRules] = useState<RuleRecord[]>([]);
  const [report, setReport] = useState<QualityReport | null>(null);
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function upload(file: File) {
    setBusyAction("upload");
    setMessage(null);
    try {
      const created = await api.uploadDataset(file);
      const loadedProfile = await api.getProfile(created.id);
      setDataset(created);
      setProfile(loadedProfile);
      setRules([]);
      setReport(null);
      setMessage(`${created.filename} is ready for review.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not upload the dataset.");
    } finally {
      setBusyAction(null);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function suggestRules() {
    if (!dataset) return;
    setBusyAction("suggest");
    setMessage(null);
    try {
      const suggested = await api.suggestRules(dataset.id);
      setRules(suggested);
      setMessage(`${suggested.length} proposed rules ready for human review.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not request suggestions.");
    } finally {
      setBusyAction(null);
    }
  }

  async function updateRule(ruleId: string, status: "approved" | "rejected") {
    setMessage(null);
    try {
      const updated = await api.updateRule(ruleId, status);
      setRules((current) => current.map((rule) => (rule.id === updated.id ? updated : rule)));
      setReport(null);
      setMessage(`Rule ${status}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not update the rule.");
    }
  }

  async function evaluate() {
    if (!dataset) return;
    setBusyAction("evaluate");
    setMessage(null);
    try {
      const createdReport = await api.evaluateDataset(dataset.id);
      setReport(createdReport);
      setMessage("Quality report generated from approved rules.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not evaluate the dataset.");
    } finally {
      setBusyAction(null);
    }
  }

  const approvedRules = rules.filter((rule) => rule.status === "approved").length;

  return (
    <main className="shell">
      <header className="topbar">
        <div className="product-lockup">
          <span className="product-mark" aria-hidden="true">◆</span>
          <div>
            <div className="brand">DataTrust</div>
            <span className="product-subtitle">Data quality workspace</span>
          </div>
        </div>
        <div className="global-search" aria-label="Workspace search">
          <span aria-hidden="true">⌕</span>
          <span>Search workspace</span>
          <kbd>⌘ K</kbd>
        </div>
        <div className="topbar-tools">
          <span className="environment">Local</span>
          <span className="avatar" aria-label="Workspace owner">DT</span>
        </div>
      </header>
      <div className="workspace">
        <nav className="sidebar" aria-label="Primary navigation">
          <div className="project-switcher">
            <span className="project-avatar">DQ</span>
            <span><strong>Data quality</strong><small>Workbench project</small></span>
            <span className="project-switcher-chevron" aria-hidden="true">⌄</span>
          </div>
          <p className="nav-label">Workspace</p>
          <a className="nav-item active" href="#workspace"><span className="nav-glyph">▦</span>Overview</a>
          <a className="nav-item" href="#rules"><span className="nav-glyph">✓</span>Quality rules {rules.length > 0 && <span className="nav-count">{rules.length}</span>}</a>
          <a className="nav-item" href="#report"><span className="nav-glyph">◫</span>Reports</a>
          <p className="nav-label nav-label-spaced">Manage</p>
          <a className="nav-item" href="#audit"><span className="nav-glyph">◷</span>Audit log</a>
          <div className="sidebar-help">
            <span className="help-icon">?</span>
            <div><strong>Review with confidence</strong><p>Rules remain proposed until you approve them.</p></div>
          </div>
        </nav>
        <section className="content" id="workspace">
          <div className="breadcrumbs"><span>Projects</span><span aria-hidden="true">/</span><span>Data quality</span><span aria-hidden="true">/</span><strong>Workspace</strong></div>
          <div className="page-heading">
            <div>
              <p className="eyebrow">Dataset review</p>
              <h1>{dataset?.filename ?? "Inspect data quality"}</h1>
              <p className="secondary">
                Profile a dataset, review suggested checks, and run an explainable quality evaluation.
              </p>
            </div>
            <div className="heading-actions"><button type="button" className="button-secondary" onClick={() => inputRef.current?.click()} disabled={busyAction === "upload"}>Replace data</button><button type="button" onClick={() => inputRef.current?.click()} disabled={busyAction === "upload"}>{busyAction === "upload" ? "Uploading…" : "Upload dataset"}</button></div>
            <input
              ref={inputRef}
              className="visually-hidden"
              id="dataset-file"
              type="file"
              accept=".csv,.json,application/json,text/csv"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void upload(file);
              }}
            />
          </div>
          {message && <div className="notice" role="status">{message}</div>}
          {dataset === null || profile === null ? (
            <section className="panel empty-state">
              <div className="empty-icon" aria-hidden="true">⇧</div>
              <p className="eyebrow">Start a review</p>
              <h2>Bring in a dataset to begin</h2>
              <p>Choose a CSV or JSON file. You will see its schema, candidate rules, evaluation results, and the decision history in one place.</p>
              <button type="button" onClick={() => inputRef.current?.click()}>Choose a dataset</button>
              <small>CSV and JSON · up to 5 MB · processed locally</small>
            </section>
          ) : (
            <div className="review-layout">
              <div className="review-canvas">
                <section className="dataset-context">
                  <span className="dataset-file-icon" aria-hidden="true">▤</span>
                  <div><strong>{dataset.filename}</strong><p>Imported and ready for human review</p></div>
                  <span className="review-state"><span aria-hidden="true">●</span> Ready</span>
                </section>
              <MetricStrip report={report} rules={rules.length} approvedRules={approvedRules} />
              <div className="dataset-summary">
                <span>{dataset.row_count.toLocaleString()} rows</span>
                <span>{dataset.column_count} columns</span>
                <span>{dataset.size_bytes.toLocaleString()} bytes</span>
                <span>Uploaded {new Date(dataset.created_at).toLocaleString()}</span>
              </div>
              <ProfileTable profile={profile} />
              <div className="two-column">
                <div id="rules">
                  <RulesPanel
                    rules={rules}
                    requestingSuggestions={busyAction === "suggest"}
                    onSuggest={() => void suggestRules()}
                    onUpdate={(ruleId, status) => void updateRule(ruleId, status)}
                  />
                </div>
                <div id="report">
                  <ReportPanel
                    report={report}
                    evaluating={busyAction === "evaluate"}
                    approvedRules={approvedRules}
                    onEvaluate={() => void evaluate()}
                  />
                </div>
              </div>
                <div id="audit"><AuditPanel rules={rules} /></div>
              </div>
              <aside className="details-rail" aria-label="Dataset details">
                <section className="details-card">
                  <div className="details-heading"><h2>Details</h2><button type="button" className="button-quiet" onClick={() => inputRef.current?.click()}>Edit</button></div>
                  <dl>
                    <div><dt>Status</dt><dd><span className="detail-status">Ready for review</span></dd></div>
                    <div><dt>Source</dt><dd>{dataset.file_type.toUpperCase()}</dd></div>
                    <div><dt>Schema</dt><dd>{dataset.column_count} fields</dd></div>
                    <div><dt>Uploaded</dt><dd>{new Date(dataset.created_at).toLocaleDateString()}</dd></div>
                  </dl>
                </section>
                <section className="details-card workflow-card">
                  <p className="eyebrow">Review progress</p>
                  <h2>Quality workflow</h2>
                  <ol className="workflow-list">
                    <li className="complete"><span>1</span><div><strong>Profile dataset</strong><small>Schema is ready</small></div></li>
                    <li className={rules.length > 0 ? "complete" : ""}><span>2</span><div><strong>Review suggestions</strong><small>{rules.length > 0 ? `${rules.length} rules available` : "Request candidate rules"}</small></div></li>
                    <li className={approvedRules > 0 ? "complete" : ""}><span>3</span><div><strong>Approve checks</strong><small>{approvedRules > 0 ? `${approvedRules} checks selected` : "Select checks to enforce"}</small></div></li>
                    <li className={report ? "complete" : ""}><span>4</span><div><strong>Run evaluation</strong><small>{report ? "Report is available" : "Generate a quality report"}</small></div></li>
                  </ol>
                </section>
              </aside>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
