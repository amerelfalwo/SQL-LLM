"use client";

import { useMemo, useState } from "react";
import { Database, Search, ChevronRight, Copy, Check, Table2, Layers, Key } from "lucide-react";
import type { TableInfo } from "@/lib/api";

interface SchemaSidebarProps {
  tables: TableInfo[];
  isOpen: boolean;
  onToggle: () => void;
}

export default function SchemaSidebar({ tables, isOpen }: SchemaSidebarProps) {
  const [search, setSearch] = useState("");
  const [openTable, setOpenTable] = useState<string | null>(null);
  const [copiedTable, setCopiedTable] = useState<string | null>(null);

  const filteredTables = useMemo(() => {
    if (!search.trim()) return tables;
    const q = search.toLowerCase();
    return tables.filter(
      (t) => t.name.toLowerCase().includes(q) || t.ddl.toLowerCase().includes(q)
    );
  }, [tables, search]);

  const copyDDL = (tableName: string, ddl: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(ddl);
    setCopiedTable(tableName);
    setTimeout(() => setCopiedTable(null), 2000);
  };

  // Extract columns roughly from CREATE TABLE statement for quick inspection
  const parseColumns = (ddl: string) => {
    const lines = ddl.split("\n");
    const cols: { name: string; type: string; isPk: boolean }[] = [];
    for (const line of lines) {
      const trimmed = line.trim().replace(/^\[|\]/g, "");
      if (
        trimmed.startsWith("CONSTRAINT") ||
        trimmed.startsWith("FOREIGN KEY") ||
        trimmed.startsWith("PRIMARY KEY") ||
        trimmed.startsWith("CREATE TABLE") ||
        trimmed === "(" ||
        trimmed === ")" ||
        !trimmed
      ) {
        continue;
      }
      const parts = trimmed.split(/\s+/);
      if (parts.length >= 2) {
        const colName = parts[0].replace(/[\[\],]/g, "");
        const colType = parts[1].replace(/[,)]/g, "");
        const isPk = trimmed.toUpperCase().includes("PRIMARY KEY") || colName.toLowerCase().endsWith("id");
        cols.push({ name: colName, type: colType, isPk });
      }
    }
    return cols.slice(0, 10); // show first 10 columns
  };

  if (!isOpen) return null;

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title-row">
          <div className="db-badge">
            <Database size={16} className="text-cyan" />
            <span>Chinook SQLite</span>
          </div>
          <span className="pill-badge">{tables.length} Tables</span>
        </div>
        <p className="sidebar-subtitle">Strict read-only safety mode</p>
      </div>

      <div className="search-wrap">
        <Search size={14} className="search-icon" />
        <input
          type="text"
          placeholder="Filter tables & columns..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="tables-list">
        {filteredTables.map((t) => {
          const isExpanded = openTable === t.name;
          const columns = isExpanded ? parseColumns(t.ddl) : [];

          return (
            <div key={t.name} className={`table-item ${isExpanded ? "active" : ""}`}>
              <button
                type="button"
                className="table-header-btn"
                onClick={() => setOpenTable(isExpanded ? null : t.name)}
              >
                <div className="table-name-wrap">
                  <Table2 size={15} className="table-icon" />
                  <span className="table-name">{t.name}</span>
                </div>
                <div className="table-actions">
                  <button
                    type="button"
                    title="Copy CREATE TABLE DDL"
                    className="icon-btn-subtle"
                    onClick={(e) => copyDDL(t.name, t.ddl, e)}
                  >
                    {copiedTable === t.name ? (
                      <Check size={13} className="text-good" />
                    ) : (
                      <Copy size={13} />
                    )}
                  </button>
                  <ChevronRight
                    size={15}
                    className={`chevron-icon ${isExpanded ? "rotated" : ""}`}
                  />
                </div>
              </button>

              {isExpanded && (
                <div className="table-expanded-content">
                  <div className="columns-summary">
                    <div className="columns-header">
                      <Layers size={12} />
                      <span>Schema Preview</span>
                    </div>
                    <div className="columns-grid">
                      {columns.map((col, idx) => (
                        <div key={idx} className="column-chip">
                          {col.isPk ? (
                            <Key size={10} className="text-amber" />
                          ) : (
                            <span className="dot-mini" />
                          )}
                          <span className="col-name">{col.name}</span>
                          <span className="col-type">{col.type}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <pre className="ddl-block">{t.ddl}</pre>
                </div>
              )}
            </div>
          );
        })}

        {filteredTables.length === 0 && (
          <div className="empty-search">
            <p>No tables match &quot;{search}&quot;</p>
          </div>
        )}
      </div>
    </aside>
  );
}
