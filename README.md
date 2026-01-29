# Jules Command Center 🤖
> Seu Arquiteto de Software Autônomo, operando 24/7 na Nuvem via WhatsApp.

Este projeto conecta o **Jules (Google DeepMind)** ao seu WhatsApp, permitindo que você gerencie tarefas de codificação, crie PRs e monitore repositórios de qualquer lugar.

---

## 🏗 Arquitetura & Infraestrutura

O sistema é construído sobre três pilares principais hospedados na nuvem:

### 1. Vercel (O Cérebro)
*   **Função**: Orquestra as requisições e hospeda a API Gateway.
*   **Endpoints**:
    *   `POST /api/webhook`: Recebe mensagens do WhatsApp. Inicia sessões no Jules e salva o estado inicial no Convex.
    *   `GET /api/cron`: Executado a cada 1 minuto (Vercel Cron). Verifica tarefas pendentes e atualiza o usuário.
*   **Deploy**: Automático via Git Push (`josepedro15/jules-command-center`).

### 2. Convex (A Memória)
*   **Função**: Banco de dados Serverless em tempo real. Mantém o estado de cada tarefa.
*   **Tabelas**: `jules_sessions` (ID, Status, Repo, Telefone).
*   **Lógica**: As funções de banco (`tasks.ts`) rodam na nuvem do Convex, garantindo consistência e rapidez.
*   **URL**: `https://charming-wolverine-788.convex.cloud` (Produção).

### 3. GitHub (O Código)
*   **Função**: Onde o código vive e onde o Jules trabalha.
*   **Integração**: Jules cria Pull Requests (PRs) diretamente nos repositórios alvo.

---

## 🔄 Fluxo de Uma Tarefa

1.  **Você (WhatsApp)**: Envia *"Refatorar o sistema de login no repo crm-pro"*.
2.  **Vercel (Webhook)**: 
    *   Recebe a mensagem.
    *   Chama a API do Jules para iniciar a sessão de IA.
    *   Escreve no **Convex**: `status: PENDING`.
    *   Responde "OK" para o WhatsApp.
3.  **Vercel (Cron Job)**:
    *   A cada minuto, pergunta ao **Convex**: "Tem tarefa pendente?"
    *   Se tiver, pergunta ao **Jules**: "Já acabou?"
    *   Se `SUCCEEDED`, manda zap pra você: "✅ Tarefa Concluída! Veja o PR."
    *   Atualiza **Convex**: `status: DONE`.

---

## 🛠 Guia de Uso e Manutenção

### Variáveis de Ambiente (Vercel)
Para que a mágica aconteça, essas chaves devem estar configuradas no painel da Vercel:

| Variável | Descrição |
| :--- | :--- |
| `JULES_API_KEY` | Autenticação com a IA do Google. |
| `CONVEX_URL` | URL do seu banco Convex (vide acima). |
| `CONVEX_ACCESS_TOKEN` | Permissão para ler/escrever no banco. |
| `GITHUB_TOKEN` | Permissão para listar repositórios. |
| `WHATSAPP_API_URL` | Endpoint da sua API de Zap. |
| `WHATSAPP_API_TOKEN` | Token de envio do Zap. |

### Comandos Úteis (Local)

Para fazer manutenção no código do banco de dados (Schema):
```bash
# 1. Instalar dependências
npm install

# 2. Subir alterações do schema para a nuvem
npx convex deploy
```

Para atualizar a lógica da API:
```bash
# Basta dar push no git!
git add .
git commit -m "feat: nova funcionalidade"
git push
```
A Vercel fará o deploy automático.
