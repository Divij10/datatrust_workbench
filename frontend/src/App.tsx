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
        <div className="brand">DataTrust Workbench</div>
        <span className="environment">Local workspace</span>
      </header>
      <div className="workspace">
        <nav className="sidebar" aria-label="Primary navigation">
          <a className="nav-item active" href="#workspace">Workspace</a>
          <a className="nav-item" href="#rules">Rules</a>
          <a className="nav-item" href="#report">Reports</a>
        </nav>
        <section className="content" id="workspace">
          <div className="page-heading">
            <div>
              <p className="eyebrow">Dataset workspace</p>
              <h1>{dataset?.filename ?? "Inspect data quality"}</h1>
              <p className="secondary">
                Upload a CSV or JSON dataset, profile its schema, then review deterministic quality checks.
              </p>
            </div>
            <button type="button" onClick={() => inputRef.current?.click()} disabled={busyAction === "upload"}>
              {busyAction === "upload" ? "Uploading…" : "Upload dataset"}
            </button>
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
              <h2>Start with a dataset</h2>
              <p>Choose a CSV or JSON file. The workspace will show its schema, potential quality rules, evaluation results, and the rule decision history.</p>
              <button type="button" onClick={() => inputRef.current?.click()}>Select file</button>
            </section>
          ) : (
            <>
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
              <AuditPanel rules={rules} />
            </>
          )}
        </section>
      </div>
    </main>
  );
}
