import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

type Metric = { label: string; value: string; note: string };

const metrics: Metric[] = [
  { label: "Quality", value: "—", note: "Evaluate approved rules" },
  { label: "Critical", value: "—", note: "No dataset selected" },
  { label: "Warnings", value: "—", note: "No dataset selected" },
];

function App() {
  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">DataTrust Workbench</div>
        <span className="status" aria-label="Demo mode enabled">Demo mode</span>
      </header>
      <div className="workspace">
        <nav className="sidebar" aria-label="Primary navigation">
          <a className="nav-item active" href="#datasets">Datasets</a>
          <a className="nav-item" href="#reports">Reports</a>
        </nav>
        <section className="content" id="datasets">
          <div className="page-heading">
            <div>
              <p className="eyebrow">Dataset workspace</p>
              <h1>Upload a dataset</h1>
              <p className="secondary">Profile CSV or JSON data before defining deterministic quality rules.</p>
            </div>
            <button type="button">Upload dataset</button>
          </div>
          <section className="upload-panel" aria-labelledby="upload-title">
            <h2 id="upload-title">No dataset selected</h2>
            <p>Choose a CSV or JSON file up to the configured size limit. Files are profiled locally.</p>
            <label className="file-picker" htmlFor="dataset-file">Select file</label>
            <input id="dataset-file" type="file" accept=".csv,.json,application/json,text/csv" />
          </section>
          <section className="metric-strip" aria-label="Dataset metrics">
            {metrics.map((metric) => (
              <div className="metric" key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
                <small>{metric.note}</small>
              </div>
            ))}
          </section>
          <section className="empty-state" id="reports">
            <h2>Profile results will appear here</h2>
            <p>Column types, null rates, distinct values, and duplicate-row counts are computed by the API.</p>
          </section>
        </section>
      </div>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
