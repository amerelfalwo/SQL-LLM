"use client";

import { useState } from "react";
import type { Execution } from "@/lib/api";

interface ResultTableProps {
  exec: Execution;
}

export default function ResultTable({ exec }: ResultTableProps) {
  const [copied, setCopied] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  if (!exec.success) {
    return (
      <div className="summary-status-strip error">
        <strong>Execution Failed:</strong> {exec.error}
      </div>
    );
  }

  if (exec.rows.length === 0) {
    return (
      <div className="results-block">
        <p className="results-count">Query executed successfully, returning 0 matching rows.</p>
      </div>
    );
  }

  const totalRows = exec.rows.length;
  const totalPages = Math.ceil(totalRows / pageSize);
  const startIdx = (page - 1) * pageSize;
  const visibleRows = exec.rows.slice(startIdx, startIdx + pageSize);

  const exportCSV = () => {
    const csvContent = [
      exec.columns.join(","),
      ...exec.rows.map((r) =>
        r.map((v) => (v === null ? "" : `"${String(v).replace(/"/g, '""')}"`)).join(",")
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `chinook_query_result.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const copyJSON = () => {
    const data = exec.rows.map((row) => {
      const obj: Record<string, unknown> = {};
      exec.columns.forEach((col, i) => {
        obj[col] = row[i];
      });
      return obj;
    });
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="results-block">
      <div className="results-top-bar">
        <span className="results-count">
          Retrieved {totalRows} row{totalRows !== 1 ? "s" : ""} in {exec.execution_time_ms.toFixed(1)} ms
        </span>

        <div className="results-tools">
          <button type="button" onClick={copyJSON} className="btn-outline-sm">
            {copied ? "Copied" : "Copy JSON"}
          </button>
          <button type="button" onClick={exportCSV} className="btn-outline-sm">
            Download CSV
          </button>
        </div>
      </div>

      <div className="table-frame">
        <table className="editorial-table">
          <thead>
            <tr>
              <th className="col-idx">#</th>
              {exec.columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((row, i) => (
              <tr key={startIdx + i}>
                <td className="col-idx">{startIdx + i + 1}</td>
                {row.map((val, j) => (
                  <td key={j}>
                    {val === null ? <span className="null-pill">NULL</span> : String(val)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination-row">
          <span>
            Page {page} of {totalPages}
          </span>
          <div className="pagination-nav">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="btn-outline-sm"
            >
              Previous
            </button>
            <span className="page-num">{page}</span>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="btn-outline-sm"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
