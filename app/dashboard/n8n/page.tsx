"use client";

import { useEffect, useState } from "react";
import { getN8NWorkflows, getN8NStats, getN8NErrors } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  Workflow, Activity, AlertTriangle, CheckCircle,
  RefreshCw, GitBranch, Loader2,
} from "lucide-react";

export default function N8NPage() {
  const [stats, setStats] = useState<any>(null);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [errors, setErrors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"workflows" | "errors">("workflows");

  async function fetchAll() {
    setLoading(true);
    try {
      const [statsData, workflowsData, errorsData] = await Promise.all([
        getN8NStats().catch(() => ({})),
        getN8NWorkflows().catch(() => []),
        getN8NErrors().catch(() => []),
      ]);
      setStats(statsData);
      setWorkflows(workflowsData);
      setErrors(errorsData);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchAll();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Workflow className="w-6 h-6 text-[var(--accent)]" />
            N8N
          </h1>
          <p className="text-[var(--text-secondary)] text-sm">
            Monitoramento de workflows (somente leitura)
          </p>
        </div>
        <button onClick={fetchAll} className="btn btn-secondary">
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Atualizar
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Workflows" value={stats?.total_workflows ?? "—"} icon={<Workflow className="w-5 h-5 text-blue-400" />} />
        <StatCard label="Ativos" value={stats?.active_workflows ?? "—"} icon={<Activity className="w-5 h-5 text-green-400" />} />
        <StatCard label="Execucoes Recentes" value={stats?.recent_executions ?? "—"} icon={<CheckCircle className="w-5 h-5 text-purple-400" />} />
        <StatCard label="Erros Recentes" value={stats?.recent_errors ?? "—"} icon={<AlertTriangle className="w-5 h-5 text-red-400" />} />
      </div>

      {/* Error Rate */}
      {stats?.error_rate !== undefined && (
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-[var(--text-secondary)]">Taxa de Erro</span>
            <span className={`font-bold ${stats.error_rate > 20 ? "text-red-400" : stats.error_rate > 5 ? "text-yellow-400" : "text-green-400"}`}>
              {stats.error_rate}%
            </span>
          </div>
          <div className="w-full bg-[var(--bg-secondary)] rounded-full h-2">
            <div
              className={`h-2 rounded-full ${stats.error_rate > 20 ? "bg-red-400" : stats.error_rate > 5 ? "bg-yellow-400" : "bg-green-400"}`}
              style={{ width: `${Math.min(stats.error_rate, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-[var(--border)] pb-0">
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === "workflows" ? "border-[var(--accent)] text-[var(--accent)]" : "border-transparent text-[var(--text-secondary)]"}`}
          onClick={() => setActiveTab("workflows")}
        >
          Workflows Sincronizados
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === "errors" ? "border-red-400 text-red-400" : "border-transparent text-[var(--text-secondary)]"}`}
          onClick={() => setActiveTab("errors")}
        >
          Erros ({errors.length})
        </button>
      </div>

      {/* Content */}
      {activeTab === "workflows" ? (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-[var(--text-secondary)]">
                <th className="text-left p-3 font-medium">Nome</th>
                <th className="text-left p-3 font-medium">ID N8N</th>
                <th className="text-left p-3 font-medium">GitHub</th>
                <th className="text-left p-3 font-medium">Sync</th>
              </tr>
            </thead>
            <tbody>
              {workflows.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-6 text-center text-[var(--text-secondary)]">
                    {loading ? "Carregando..." : "Nenhum workflow sincronizado ainda"}
                  </td>
                </tr>
              ) : (
                workflows.map((wf: any) => (
                  <tr key={wf.id} className="border-b border-[var(--border)] hover:bg-[var(--bg-card-hover)]">
                    <td className="p-3 font-medium">{wf.name}</td>
                    <td className="p-3 text-[var(--text-secondary)] font-mono text-xs">{wf.n8n_workflow_id}</td>
                    <td className="p-3">
                      {wf.github_repo ? (
                        <span className="flex items-center gap-1 text-green-400 text-xs">
                          <GitBranch className="w-3 h-3" />
                          {wf.github_repo}
                        </span>
                      ) : (
                        <span className="text-[var(--text-secondary)] text-xs">—</span>
                      )}
                    </td>
                    <td className="p-3">
                      <span className={`badge ${wf.github_synced ? "badge-success" : "badge-warning"}`}>
                        {wf.github_synced ? "Sincronizado" : "Pendente"}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="space-y-3">
          {errors.length === 0 ? (
            <div className="card text-center text-[var(--text-secondary)]">
              Nenhum erro recente
            </div>
          ) : (
            errors.map((err: any, i: number) => (
              <div key={i} className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                      <span className="font-medium text-sm">
                        {err.workflowData?.name || "Workflow Desconhecido"}
                      </span>
                    </div>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">
                      {err.stoppedAt ? formatDate(err.stoppedAt) : "Data desconhecida"}
                    </p>
                  </div>
                  <span className="badge badge-error">Erro</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string; value: any; icon: React.ReactNode }) {
  return (
    <div className="card flex items-center gap-3">
      {icon}
      <div>
        <p className="text-xl font-bold">{value}</p>
        <p className="text-xs text-[var(--text-secondary)]">{label}</p>
      </div>
    </div>
  );
}
