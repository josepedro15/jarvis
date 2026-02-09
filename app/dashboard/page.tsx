"use client";

import { useEffect, useState } from "react";
import { getDashboard } from "@/lib/api";
import { formatDate, statusColor } from "@/lib/utils";
import {
  GitBranch, Workflow, MessageSquare, AlertTriangle,
  CheckCircle, Clock, XCircle, Activity,
} from "lucide-react";

export default function DashboardPage() {
  const [data, setData] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-[var(--text-secondary)]">Carregando...</div>
      </div>
    );
  }

  const jules = data?.jules || { pending: 0, recent: [] };
  const n8n = data?.n8n || {};
  const logs = data?.recent_logs || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-[var(--text-secondary)] text-sm">Visao geral do Jarvis</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<Clock className="w-5 h-5 text-yellow-400" />}
          label="Jules Pendentes"
          value={jules.pending}
          color="yellow"
        />
        <MetricCard
          icon={<Workflow className="w-5 h-5 text-blue-400" />}
          label="Workflows N8N"
          value={n8n.total_workflows ?? "—"}
          color="blue"
        />
        <MetricCard
          icon={<Activity className="w-5 h-5 text-green-400" />}
          label="Workflows Ativos"
          value={n8n.active_workflows ?? "—"}
          color="green"
        />
        <MetricCard
          icon={<AlertTriangle className="w-5 h-5 text-red-400" />}
          label="Erros N8N"
          value={n8n.recent_errors ?? "—"}
          color="red"
        />
      </div>

      {/* Two columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Jules Sessions */}
        <div className="card">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-[var(--accent)]" />
            Tarefas Jules Recentes
          </h2>
          {jules.recent?.length === 0 ? (
            <p className="text-sm text-[var(--text-secondary)]">Nenhuma tarefa ainda</p>
          ) : (
            <div className="space-y-3">
              {jules.recent?.slice(0, 5).map((session: any) => (
                <div key={session.id} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 min-w-0">
                    <StatusIcon status={session.status} />
                    <span className="truncate">
                      {session.repo_name?.replace("github/", "").replace("josepedro15/", "")}
                    </span>
                  </div>
                  <span className={`text-xs ${statusColor(session.status)}`}>
                    {session.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Logs */}
        <div className="card">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-[var(--accent)]" />
            Logs Recentes
          </h2>
          {logs.length === 0 ? (
            <p className="text-sm text-[var(--text-secondary)]">Nenhum log ainda</p>
          ) : (
            <div className="space-y-2">
              {logs.slice(0, 8).map((log: any) => (
                <div key={log.id} className="text-xs flex items-start gap-2">
                  <span className={`badge ${
                    log.level === "error" ? "badge-error" :
                    log.level === "warn" ? "badge-warning" : "badge-info"
                  }`}>
                    {log.level}
                  </span>
                  <span className="text-[var(--text-secondary)] shrink-0">{log.source}</span>
                  <span className="truncate">{log.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  icon, label, value, color,
}: {
  icon: React.ReactNode; label: string; value: string | number; color: string;
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-${color}-400/10`}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs text-[var(--text-secondary)]">{label}</p>
      </div>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "SUCCEEDED":
    case "COMPLETED":
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    case "FAILED":
      return <XCircle className="w-4 h-4 text-red-400" />;
    case "PENDING":
      return <Clock className="w-4 h-4 text-yellow-400" />;
    default:
      return <Activity className="w-4 h-4 text-gray-400" />;
  }
}
