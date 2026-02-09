"use client";

import { useEffect, useState } from "react";
import { getLogs } from "@/lib/api";
import { formatDate, levelColor } from "@/lib/utils";
import { ScrollText, RefreshCw, Filter } from "lucide-react";

export default function LogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sourceFilter, setSourceFilter] = useState("");
  const [levelFilter, setLevelFilter] = useState("");

  async function fetchLogs() {
    setLoading(true);
    try {
      const data = await getLogs(sourceFilter || undefined, levelFilter || undefined, 200);
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchLogs();
    // Auto-refresh a cada 10 segundos
    const interval = setInterval(fetchLogs, 10000);
    return () => clearInterval(interval);
  }, [sourceFilter, levelFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ScrollText className="w-6 h-6 text-[var(--accent)]" />
            Logs do Sistema
          </h1>
          <p className="text-[var(--text-secondary)] text-sm">
            Monitoramento em tempo real (atualiza a cada 10s)
          </p>
        </div>
        <button onClick={fetchLogs} className="btn btn-secondary">
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Atualizar
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <Filter className="w-4 h-4 text-[var(--text-secondary)]" />
        <select
          className="input w-auto"
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
        >
          <option value="">Todas as fontes</option>
          <option value="whatsapp">WhatsApp</option>
          <option value="jules">Jules</option>
          <option value="n8n">N8N</option>
          <option value="github">GitHub</option>
          <option value="ai">IA</option>
        </select>

        <select
          className="input w-auto"
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
        >
          <option value="">Todos os niveis</option>
          <option value="info">Info</option>
          <option value="warn">Warning</option>
          <option value="error">Error</option>
          <option value="debug">Debug</option>
        </select>

        <span className="text-xs text-[var(--text-secondary)]">
          {logs.length} registro(s)
        </span>
      </div>

      {/* Logs Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-[var(--text-secondary)]">
                <th className="text-left p-3 font-medium">Data</th>
                <th className="text-left p-3 font-medium">Nivel</th>
                <th className="text-left p-3 font-medium">Fonte</th>
                <th className="text-left p-3 font-medium">Mensagem</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-6 text-center text-[var(--text-secondary)]">
                    {loading ? "Carregando..." : "Nenhum log encontrado"}
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="border-b border-[var(--border)] hover:bg-[var(--bg-card-hover)]">
                    <td className="p-3 text-xs text-[var(--text-secondary)] whitespace-nowrap">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="p-3">
                      <span className={`badge ${
                        log.level === "error" ? "badge-error" :
                        log.level === "warn" ? "badge-warning" :
                        log.level === "debug" ? "badge-neutral" : "badge-info"
                      }`}>
                        {log.level}
                      </span>
                    </td>
                    <td className="p-3 text-[var(--text-secondary)]">{log.source}</td>
                    <td className="p-3 max-w-md truncate">{log.message}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
