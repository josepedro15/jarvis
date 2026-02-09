"use client";

import { useEffect, useState } from "react";
import { getJulesSessions } from "@/lib/api";
import { formatDate, statusColor } from "@/lib/utils";
import {
  GitBranch, CheckCircle, Clock, XCircle,
  ExternalLink, RefreshCw, Activity, Ban,
} from "lucide-react";

export default function JulesPage() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  async function fetchSessions() {
    setLoading(true);
    try {
      const data = await getJulesSessions();
      setSessions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchSessions();
    const interval = setInterval(fetchSessions, 30000); // Atualiza a cada 30s
    return () => clearInterval(interval);
  }, []);

  const filtered = filter === "all" ? sessions : sessions.filter((s) => s.status === filter);

  const counts = {
    all: sessions.length,
    PENDING: sessions.filter((s) => s.status === "PENDING").length,
    COMPLETED: sessions.filter((s) => ["COMPLETED", "SUCCEEDED"].includes(s.status)).length,
    FAILED: sessions.filter((s) => s.status === "FAILED").length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <GitBranch className="w-6 h-6 text-[var(--accent)]" />
            Jules - Tarefas
          </h1>
          <p className="text-[var(--text-secondary)] text-sm">
            Historico de sessoes de coding (atualiza a cada 30s)
          </p>
        </div>
        <button onClick={fetchSessions} className="btn btn-secondary">
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Atualizar
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <button onClick={() => setFilter("all")} className={`card cursor-pointer ${filter === "all" ? "!border-[var(--accent)]" : ""}`}>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-400" />
            <span className="text-lg font-bold">{counts.all}</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)]">Total</p>
        </button>
        <button onClick={() => setFilter("PENDING")} className={`card cursor-pointer ${filter === "PENDING" ? "!border-yellow-400" : ""}`}>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-yellow-400" />
            <span className="text-lg font-bold">{counts.PENDING}</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)]">Pendentes</p>
        </button>
        <button onClick={() => setFilter("COMPLETED")} className={`card cursor-pointer ${filter === "COMPLETED" ? "!border-green-400" : ""}`}>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span className="text-lg font-bold">{counts.COMPLETED}</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)]">Concluidas</p>
        </button>
        <button onClick={() => setFilter("FAILED")} className={`card cursor-pointer ${filter === "FAILED" ? "!border-red-400" : ""}`}>
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-red-400" />
            <span className="text-lg font-bold">{counts.FAILED}</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)]">Falharam</p>
        </button>
      </div>

      {/* Sessions List */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <div className="card text-center text-[var(--text-secondary)]">
            {loading ? "Carregando..." : "Nenhuma tarefa encontrada"}
          </div>
        ) : (
          filtered.map((session: any) => (
            <div key={session.id} className="card">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <StatusIcon status={session.status} />
                    <span className="font-medium">
                      {session.repo_name?.replace("github/", "").replace("josepedro15/", "")}
                    </span>
                    <span className={`badge ${
                      ["COMPLETED", "SUCCEEDED"].includes(session.status) ? "badge-success" :
                      session.status === "PENDING" ? "badge-warning" :
                      session.status === "FAILED" ? "badge-error" : "badge-neutral"
                    }`}>
                      {session.status}
                    </span>
                  </div>

                  {session.task_description && (
                    <p className="text-sm text-[var(--text-secondary)]">
                      {session.task_description}
                    </p>
                  )}

                  <div className="flex items-center gap-4 text-xs text-[var(--text-secondary)]">
                    <span>Inicio: {formatDate(session.started_at)}</span>
                    {session.completed_at && (
                      <span>Fim: {formatDate(session.completed_at)}</span>
                    )}
                  </div>
                </div>

                {session.pr_url && (
                  <a
                    href={session.pr_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-secondary text-xs"
                  >
                    <ExternalLink className="w-3 h-3" />
                    Ver PR
                  </a>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "SUCCEEDED":
    case "COMPLETED":
      return <CheckCircle className="w-5 h-5 text-green-400" />;
    case "FAILED":
      return <XCircle className="w-5 h-5 text-red-400" />;
    case "CANCELLED":
      return <Ban className="w-5 h-5 text-gray-400" />;
    case "PENDING":
      return <Clock className="w-5 h-5 text-yellow-400 animate-pulse" />;
    default:
      return <Activity className="w-5 h-5 text-gray-400" />;
  }
}
