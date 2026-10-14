"use client";

import { useCallback, useEffect, useState } from "react";
import ResultTable from "@/components/ResultTable";
import {
  api,
  type AskResponse,
  type Execution,
  type HealthResponse,
  type TableInfo,
} from "@/lib/api";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [examples, setExamples] = useState<string[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [sql, setSql] = useState("");
  const [rerun, setRerun] = useState<Execution | null>(null);
  const [rerunLoading, setRerunLoading] = useState(false);
  const [colabUrl, setColabUrl] = useState("");
  const [showConfig, setShowConfig] = useState(false);
  const [copiedSql, setCopiedSql] = useState(false);
  const [activeSchemaTable, setActiveSchemaTable] = useState<string | null>(null);

  const refreshHealth = useCallback(() => {
    api
      .health()
      .then((h) => {
        setHealth(h);
        if (!h.colab_configured) {
          setShowConfig(true);
        }
      })
      .catch((e: Error) => {
        setHealth(null);
        setError(e.message);
      });
  }, []);

  useEffect(() => {
    refreshHealth();
    api
      .schema()
      .then((s) => setTables(s.tables))
      .catch(() => undefined);
    api
      .examples()
      .then((e) => setExamples(e.examples))
      .catch(() => undefined);
  }, [refreshHealth]);

  const ask = async (q: string) => {
    const query = q.trim();
    if (!query || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setRerun(null);
    try {
      const res = await api.ask(query);
      setResult(res);
      setSql(res.sql);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const runEdited = async () => {
    if (!sql.trim() || rerunLoading) return;
    setRerunLoading(true);
    setError(null);
    try {
      const res = await api.execute(sql.trim());
      setRerun(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRerunLoading(false);
    }
  };

  const connectColab = async () => {
    if (!colabUrl.trim()) return;
    setError(null);
    try {
      await api.setColabUrl(colabUrl.trim());
      refreshHealth();
      setShowConfig(false);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const copySql = () => {
    if (!sql) return;
    navigator.clipboard.writeText(sql);
    setCopiedSql(true);
    setTimeout(() => setCopiedSql(false), 2000);
  };

  const modelOk = health?.model?.status === "healthy";
  const activeExecution = rerun ?? result?.execution ?? null;

  return (
    <div className="page-container">
      {/* 1. Editorial Header */}
      <header className="editorial-header">
        <div className="header-left">
          <div className="meta-crumb">
            <span>Portfolio &amp; Research</span>
            <span className="crumb-dot" />
            <span>SQLite Evaluation</span>
            <span className="crumb-dot" />
            <span>Gretel AI Dataset</span>
          </div>

          <h1 className="main-title">
            Qwen2.5-Coder-3B <em>Text-to-SQL</em>
          </h1>

          <p className="lead-desc">
            A low-rank adaptation (LoRA) fine-tuned on 6,330 gold SQL pairs to translate
            natural language into deterministic SQLite queries. Below is an interactive technical
            walkthrough and evaluation laboratory on the 11-table Chinook relational database.
          </p>
        </div>

        <div className="header-actions">
          <button
            type="button"
            onClick={() => setShowConfig((v) => !v)}
            className={`status-badge ${modelOk ? "online" : "offline"}`}
            title="Configure Colab Endpoint"
          >
            <span className="status-indicator-dot" />
            <span>{modelOk ? "Colab GPU Active" : "Connect Endpoint"}</span>
          </button>
        </div>
      </header>

      {/* Optional Colab Config Drawer */}
      {showConfig && (
        <section className="minimal-config-card">
          <div className="section-head">
            <h3 className="config-title">Google Colab Inference Endpoint</h3>
            <button
              type="button"
              onClick={() => setShowConfig(false)}
              className="btn-outline-sm"
            >
              Close
            </button>
          </div>
          <p className="metric-sub">
            Paste the public ngrok URL generated from <code>colab/notebook.ipynb</code> to route natural language queries directly to the GPU.
          </p>
          <div className="config-input-group">
            <input
              type="url"
              placeholder="https://xxxx.ngrok-free.dev"
              value={colabUrl}
              onChange={(e) => setColabUrl(e.target.value)}
              className="minimal-input"
            />
            <button
              type="button"
              onClick={connectColab}
              disabled={!colabUrl.startsWith("http")}
              className="btn-solid"
            >
              Save &amp; Connect
            </button>
          </div>
        </section>
      )}

      {/* 2. Research Benchmark Metrics (Bento Grid) */}
      <section className="metrics-section">
        <div className="metric-card">
          <span className="metric-label">Chinook Execution Accuracy</span>
          <div className="metric-value-row">
            <span className="metric-number">77.5%</span>
            <span className="metric-delta">31 / 40 Strict</span>
          </div>
          <span className="metric-sub">Strict result set match (95% CI: [62.5%, 87.7%], n=40 sample database).</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Chinook Valid SQL Rate</span>
          <div className="metric-value-row">
            <span className="metric-number">85.0%</span>
            <span className="metric-delta">34 / 40</span>
          </div>
          <span className="metric-sub">34 of 40 queries executed cleanly against SQLite without syntax or schema errors.</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Synthetic Test Set</span>
          <div className="metric-value-row">
            <span className="metric-number">69.5%</span>
            <span className="metric-delta">+12.5%</span>
          </div>
          <span className="metric-sub">Compared to 57.0% base model on 200 in-distribution held-out queries.</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Training Budget</span>
          <div className="metric-value-row">
            <span className="metric-number">6,330</span>
            <span className="metric-delta">r=16</span>
          </div>
          <span className="metric-sub">Gold pairs, 1 epoch, 396 steps on a Colab L4 (Qwen2.5-Coder-3B).</span>
        </div>
      </section>

      {/* 3. Interactive Laboratory (Explainer & Live Execution) */}
      <section className="section-wrapper">
        <div className="section-head">
          <h2 className="section-title">Query Laboratory</h2>
          <span className="section-note">Live inference against Chinook SQLite</span>
        </div>

        <div className="playground-card">
          <div className="playground-input-area">
            <div className="input-label-row">
              <label htmlFor="nl-query" className="input-label">
                Natural Language Query
              </label>
              <span className="kbd-badge">Press Enter to run</span>
            </div>

            <textarea
              id="nl-query"
              rows={2}
              placeholder="e.g. Which 5 customers have the highest total invoice spending?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  ask(question);
                }
              }}
              className="natural-textarea"
            />

            <div className="input-action-row">
              <div className="examples-container">
                <span className="examples-pills-label">Curated test prompts:</span>
                <div className="pill-list">
                  {examples.slice(0, 5).map((ex, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => {
                        setQuestion(ex);
                        ask(ex);
                      }}
                      className="natural-chip"
                    >
                      {ex}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                disabled={loading || !question.trim()}
                onClick={() => ask(question)}
                className="btn-solid"
              >
                {loading ? "Generating..." : "Generate SQL"}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="summary-status-strip error">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="warm-loading-state">
              <div className="loading-bar-indicator" />
              <div>
                <p className="loading-title">Extracting Schema &amp; Generating SQL</p>
                <p className="loading-desc">Invoking Qwen2.5-Coder-3B with LoRA weights on Colab GPU...</p>
              </div>
            </div>
          )}

          {/* Generated SQL & Result Panel */}
          {result && (
            <div className="sql-output-panel">
              <div className="sql-header-bar">
                <div>
                  <span className="sql-title-tag">Generated SQL Query</span>
                  <span className="sql-timing-tag">{result.inference_time_ms.toFixed(0)} ms inference</span>
                </div>

                <div className="sql-actions-group">
                  <button type="button" onClick={copySql} className="btn-outline-sm">
                    {copiedSql ? "Copied" : "Copy SQL"}
                  </button>
                  <button
                    type="button"
                    disabled={rerunLoading || !sql.trim()}
                    onClick={runEdited}
                    className="btn-run-sm"
                  >
                    {rerunLoading ? "Executing..." : "Run Query"}
                  </button>
                </div>
              </div>

              <div className="sql-code-container">
                <textarea
                  value={sql}
                  onChange={(e) => setSql(e.target.value)}
                  spellCheck={false}
                  rows={Math.max(2, sql.split("\n").length)}
                  className="sql-editable-input"
                />
              </div>

              <div className={`summary-status-strip ${activeExecution?.success ? "success" : "error"}`}>
                {result.summary}
              </div>

              {activeExecution && <ResultTable exec={activeExecution} />}
            </div>
          )}
        </div>
      </section>

      {/* 4. How It Works (Methodology & Architecture Explanation) */}
      <section className="section-wrapper">
        <div className="section-head">
          <h2 className="section-title">System Architecture</h2>
          <span className="section-note">End-to-end data pipeline</span>
        </div>

        <div className="explainer-grid">
          <div className="explainer-card">
            <span className="explainer-step">Step 01 / Schema Introspection</span>
            <h3 className="explainer-title">Contextual DDL Extraction</h3>
            <p className="explainer-body">
              Before calling the model, the backend reads SQLite system catalog (<code>sqlite_master</code>)
              and supplies exact <code>CREATE TABLE</code> definitions so the model is aware of
              foreign keys, primary keys, and exact column namings.
            </p>
          </div>

          <div className="explainer-card">
            <span className="explainer-step">Step 02 / Bound Prompting</span>
            <h3 className="explainer-title">Exact Token Objective</h3>
            <p className="explainer-body">
              Prompts follow the exact training format: <code>System: You are a SQL assistant... User: Schema:\n&lt;DDL&gt;\n\nQuestion:&lt;question&gt;</code>.
              Greedy decoding (<code>do_sample=False</code>) ensures reproducible, deterministic query construction.
            </p>
          </div>

          <div className="explainer-card">
            <span className="explainer-step">Step 03 / Sandboxed Safety</span>
            <h3 className="explainer-title">Strict Read-Only Execution</h3>
            <p className="explainer-body">
              The model-generated query is executed using SQLite URI read-only mode (<code>mode=ro</code>)
              with an upfront blocklist for write operations (<code>DROP</code>, <code>DELETE</code>, <code>UPDATE</code>, <code>INSERT</code>), guaranteeing safe evaluations.
            </p>
          </div>
        </div>
      </section>

      {/* 5. Database Schema Catalog */}
      <section className="section-wrapper">
        <div className="section-head">
          <h2 className="section-title">Chinook Database Catalog</h2>
          <span className="section-note">{tables.length} Relational Tables</span>
        </div>

        <div className="schema-reference-card">
          <p className="metric-sub">
            Click any table below to inspect its schema and relational structure:
          </p>

          <div className="schema-tables-summary">
            {tables.map((t) => (
              <button
                key={t.name}
                type="button"
                onClick={() =>
                  setActiveSchemaTable(activeSchemaTable === t.name ? null : t.name)
                }
                className="table-tag"
                style={{ cursor: "pointer" }}
              >
                <strong>{t.name}</strong>
                <span>{activeSchemaTable === t.name ? "▲" : "▼"}</span>
              </button>
            ))}
          </div>

          {activeSchemaTable && (
            <div style={{ marginTop: "12px" }}>
              <pre
                style={{
                  background: "var(--canvas)",
                  padding: "16px",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border)",
                  fontSize: "0.82rem",
                  fontFamily: "ui-monospace, monospace",
                  overflowX: "auto",
                  color: "var(--ink-primary)",
                }}
              >
                {tables.find((t) => t.name === activeSchemaTable)?.ddl}
              </pre>
            </div>
          )}
        </div>
      </section>

      {/* 6. Editorial Footer */}
      <footer className="editorial-footer">
        <div>
          <span>Model: amer003100/qwen2.5-coder-3b-text-to-sql-lora</span>
        </div>

        <div className="footer-links">
          <a
            href="https://huggingface.co/amer003100/qwen2.5-coder-3b-text-to-sql-lora"
            target="_blank"
            rel="noreferrer"
            className="footer-link"
          >
            Hugging Face Adapter
          </a>
          <a
            href="https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct"
            target="_blank"
            rel="noreferrer"
            className="footer-link"
          >
            Base Qwen2.5-Coder
          </a>
          <a
            href="https://huggingface.co/datasets/gretelai/synthetic_text_to_sql"
            target="_blank"
            rel="noreferrer"
            className="footer-link"
          >
            Gretel Dataset
          </a>
        </div>
      </footer>
    </div>
  );
}
