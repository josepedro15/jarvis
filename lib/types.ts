export interface AIConfig {
  id: string;
  model: string;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  updated_at: string;
}

export interface JulesSession {
  id: string;
  session_id: string;
  repo_name: string;
  task_description: string;
  status: string;
  phone_number: string;
  pr_url: string | null;
  started_at: string;
  completed_at: string | null;
  metadata: Record<string, unknown>;
}

export interface SystemLog {
  id: string;
  level: string;
  source: string;
  message: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface AllowedNumber {
  id: string;
  phone_number: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

export interface N8NWorkflow {
  id: string;
  n8n_workflow_id: string;
  name: string;
  content: Record<string, unknown>;
  github_repo: string | null;
  github_synced: boolean;
  last_synced_at: string | null;
  created_at: string;
}

export interface Metrics {
  id: string;
  period: string;
  repos_created: number;
  jules_tasks_completed: number;
  jules_tasks_failed: number;
  n8n_workflows_synced: number;
  n8n_errors: number;
  messages_exchanged: number;
  created_at: string;
}

export interface DashboardData {
  jules: {
    pending: number;
    recent: JulesSession[];
  };
  n8n: {
    total_workflows: number;
    active_workflows: number;
    recent_executions: number;
    recent_errors: number;
    error_rate: number;
  };
  whatsapp: Record<string, unknown>;
  recent_logs: SystemLog[];
}
