"use client";

import { useEffect, useState } from "react";
import { getAIConfig, updateAIConfig, testAI } from "@/lib/api";
import { Bot, Save, FlaskConical, Loader2 } from "lucide-react";

export default function AIConfigPage() {
  const [config, setConfig] = useState({
    model: "gemini-2.5-flash",
    system_prompt: "",
    temperature: 0.7,
    max_tokens: 2048,
  });
  const [testMessage, setTestMessage] = useState("");
  const [testResponse, setTestResponse] = useState("");
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getAIConfig()
      .then((data: any) => setConfig(data))
      .catch(console.error);
  }, []);

  async function handleSave() {
    setSaving(true);
    try {
      await updateAIConfig(config);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    if (!testMessage.trim()) return;
    setTesting(true);
    setTestResponse("");
    try {
      const result = await testAI(testMessage, config.system_prompt);
      setTestResponse(result.response);
    } catch (err) {
      setTestResponse("Erro ao testar: " + String(err));
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Bot className="w-6 h-6 text-[var(--accent)]" />
          Configuracao da IA
        </h1>
        <p className="text-[var(--text-secondary)] text-sm">
          Ajuste o comportamento do Jarvis
        </p>
      </div>

      {/* Config Form */}
      <div className="card space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Modelo</label>
            <select
              className="input"
              value={config.model}
              onChange={(e) => setConfig({ ...config, model: e.target.value })}
            >
              <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
              <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
              <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">
              Temperatura: {config.temperature}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              className="w-full accent-[var(--accent)]"
              value={config.temperature}
              onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
            />
          </div>

          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Max Tokens</label>
            <input
              type="number"
              className="input"
              value={config.max_tokens}
              onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) })}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm text-[var(--text-secondary)] mb-1">System Prompt</label>
          <textarea
            className="textarea"
            style={{ minHeight: "200px" }}
            value={config.system_prompt}
            onChange={(e) => setConfig({ ...config, system_prompt: e.target.value })}
          />
        </div>

        <div className="flex items-center gap-3">
          <button onClick={handleSave} disabled={saving} className="btn btn-primary">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {saving ? "Salvando..." : "Salvar"}
          </button>
          {saved && <span className="text-sm text-green-400">Salvo com sucesso!</span>}
        </div>
      </div>

      {/* Test Area */}
      <div className="card space-y-4">
        <h2 className="font-semibold flex items-center gap-2">
          <FlaskConical className="w-4 h-4 text-[var(--accent)]" />
          Testar Prompt
        </h2>

        <div className="flex gap-3">
          <input
            type="text"
            className="input flex-1"
            placeholder="Digite uma mensagem de teste..."
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleTest()}
          />
          <button onClick={handleTest} disabled={testing} className="btn btn-secondary">
            {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : "Testar"}
          </button>
        </div>

        {testResponse && (
          <div className="bg-[var(--bg-secondary)] rounded-lg p-4 text-sm whitespace-pre-wrap">
            {testResponse}
          </div>
        )}
      </div>
    </div>
  );
}
