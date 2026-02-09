-- ============================================
-- JARVIS - Centro de Comando
-- Schema Inicial do Banco de Dados
-- ============================================

-- Numeros autorizados para interagir via WhatsApp
CREATE TABLE IF NOT EXISTS allowed_numbers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number TEXT UNIQUE NOT NULL,
    name TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Configuracao da IA (singleton - 1 registro)
CREATE TABLE IF NOT EXISTS ai_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model TEXT DEFAULT 'gemini-2.5-flash',
    system_prompt TEXT NOT NULL,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2048,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Historico de conversas
CREATE TABLE IF NOT EXISTS conversation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    intent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Sessoes do Jules
CREATE TABLE IF NOT EXISTS jules_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    repo_name TEXT NOT NULL,
    task_description TEXT,
    status TEXT DEFAULT 'PENDING',
    phone_number TEXT,
    pr_url TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

-- Workflows do N8N sincronizados
CREATE TABLE IF NOT EXISTS n8n_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    n8n_workflow_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    content JSONB NOT NULL,
    github_repo TEXT,
    github_synced BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Logs do sistema
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level TEXT DEFAULT 'info',
    source TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Metricas agregadas
CREATE TABLE IF NOT EXISTS metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period TEXT NOT NULL,
    repos_created INTEGER DEFAULT 0,
    jules_tasks_completed INTEGER DEFAULT 0,
    jules_tasks_failed INTEGER DEFAULT 0,
    n8n_workflows_synced INTEGER DEFAULT 0,
    n8n_errors INTEGER DEFAULT 0,
    messages_exchanged INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Estado de conversacao (para state machine)
CREATE TABLE IF NOT EXISTS conversation_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number TEXT UNIQUE NOT NULL,
    current_state TEXT DEFAULT 'idle',
    state_data JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indice para performance
CREATE INDEX IF NOT EXISTS idx_conversation_history_phone ON conversation_history(phone_number, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jules_sessions_status ON jules_sessions(status);
CREATE INDEX IF NOT EXISTS idx_system_logs_created ON system_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_system_logs_source ON system_logs(source);
CREATE INDEX IF NOT EXISTS idx_n8n_workflows_synced ON n8n_workflows(github_synced);

-- Inserir config padrao da IA
INSERT INTO ai_config (model, system_prompt, temperature, max_tokens)
VALUES (
    'gemini-2.5-flash',
    'Voce e o Jarvis, um assistente de IA pessoal e centro de comando. Voce gerencia tarefas de codigo via Jules, monitora workflows do N8N, e interage de forma natural e amigavel em portugues. Voce tem acesso a: GitHub (repositorios), Jules (tarefas de codigo), N8N (workflows, somente leitura), e Vercel (deploys). Sempre confirme acoes importantes antes de executar. Seja conciso nas respostas via WhatsApp.',
    0.7,
    2048
)
ON CONFLICT DO NOTHING;

-- Inserir numero autorizado padrao
INSERT INTO allowed_numbers (phone_number, name, is_active)
VALUES ('553194959512', 'Jose Pedro', true)
ON CONFLICT DO NOTHING;
