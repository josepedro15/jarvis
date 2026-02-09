/**
 * Jarvis - API Client (Frontend)
 * Funcoes para comunicacao com o backend FastAPI.
 */

const API_BASE = "/api/admin";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// --- Dashboard ---
export const getDashboard = () => fetchAPI<Record<string, unknown>>("/dashboard");

// --- AI Config ---
export const getAIConfig = () => fetchAPI<Record<string, unknown>>("/ai-config");
export const updateAIConfig = (data: Record<string, unknown>) =>
  fetchAPI("/ai-config", { method: "PUT", body: JSON.stringify(data) });
export const testAI = (message: string, systemPrompt?: string) =>
  fetchAPI<{ response: string }>("/ai-test", {
    method: "POST",
    body: JSON.stringify({ message, system_prompt: systemPrompt }),
  });

// --- WhatsApp ---
export const getWhatsAppStatus = () => fetchAPI<Record<string, unknown>>("/whatsapp/status");
export const connectWhatsApp = () =>
  fetchAPI<Record<string, unknown>>("/whatsapp/connect", { method: "POST" });
export const disconnectWhatsApp = () =>
  fetchAPI<Record<string, unknown>>("/whatsapp/disconnect", { method: "POST" });
export const configureWebhook = (url: string) =>
  fetchAPI("/whatsapp/webhook-config", {
    method: "POST",
    body: JSON.stringify({ url }),
  });

// --- Whitelist ---
export const getWhitelist = () => fetchAPI<Record<string, unknown>[]>("/whitelist");
export const addToWhitelist = (phone: string, name: string) =>
  fetchAPI("/whitelist", {
    method: "POST",
    body: JSON.stringify({ phone_number: phone, name }),
  });
export const removeFromWhitelist = (phone: string) =>
  fetchAPI(`/whitelist/${phone}`, { method: "DELETE" });

// --- Jules ---
export const getJulesSessions = () => fetchAPI<Record<string, unknown>[]>("/jules/sessions");
export const getJulesRepos = () => fetchAPI<Record<string, unknown>[]>("/jules/repos");

// --- N8N ---
export const getN8NWorkflows = () => fetchAPI<Record<string, unknown>[]>("/n8n/workflows");
export const getN8NStats = () => fetchAPI<Record<string, unknown>>("/n8n/stats");
export const getN8NErrors = () => fetchAPI<Record<string, unknown>[]>("/n8n/errors");

// --- GitHub ---
export const getGitHubRepos = () => fetchAPI<Record<string, unknown>[]>("/github/repos");

// --- Logs ---
export const getLogs = (source?: string, level?: string, limit = 100) => {
  const params = new URLSearchParams();
  if (source) params.set("source", source);
  if (level) params.set("level", level);
  params.set("limit", String(limit));
  return fetchAPI<Record<string, unknown>[]>(`/logs?${params}`);
};

// --- Metrics ---
export const getMetrics = (period?: string) => {
  const params = period ? `?period=${period}` : "";
  return fetchAPI<Record<string, unknown>[]>(`/metrics${params}`);
};
