"use client";

import { useEffect, useState } from "react";
import {
  getWhatsAppStatus, connectWhatsApp, disconnectWhatsApp,
  configureWebhook, getWhitelist, addToWhitelist, removeFromWhitelist,
} from "@/lib/api";
import {
  MessageSquare, Wifi, WifiOff, QrCode,
  Plus, Trash2, Shield, Loader2, Link,
} from "lucide-react";

export default function WhatsAppPage() {
  const [status, setStatus] = useState<any>(null);
  const [qrData, setQrData] = useState<any>(null);
  const [whitelist, setWhitelist] = useState<any[]>([]);
  const [webhookUrl, setWebhookUrl] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newName, setNewName] = useState("");
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    fetchAll();
  }, []);

  async function fetchAll() {
    setLoading(true);
    try {
      const [statusData, whitelistData] = await Promise.all([
        getWhatsAppStatus().catch(() => ({})),
        getWhitelist().catch(() => []),
      ]);
      setStatus(statusData);
      setWhitelist(whitelistData);
    } finally {
      setLoading(false);
    }
  }

  async function handleConnect() {
    setConnecting(true);
    try {
      const result = await connectWhatsApp();
      setQrData(result);
    } catch (err) {
      console.error(err);
    } finally {
      setConnecting(false);
    }
  }

  async function handleDisconnect() {
    try {
      await disconnectWhatsApp();
      setStatus({ connected: false });
      setQrData(null);
    } catch (err) {
      console.error(err);
    }
  }

  async function handleWebhookConfig() {
    if (!webhookUrl) return;
    try {
      await configureWebhook(webhookUrl);
      alert("Webhook configurado com sucesso!");
    } catch (err) {
      console.error(err);
    }
  }

  async function handleAddNumber() {
    if (!newPhone) return;
    try {
      await addToWhitelist(newPhone, newName);
      setNewPhone("");
      setNewName("");
      const updated = await getWhitelist();
      setWhitelist(updated);
    } catch (err) {
      console.error(err);
    }
  }

  async function handleRemoveNumber(phone: string) {
    if (!confirm(`Remover ${phone} da whitelist?`)) return;
    try {
      await removeFromWhitelist(phone);
      const updated = await getWhitelist();
      setWhitelist(updated);
    } catch (err) {
      console.error(err);
    }
  }

  const isConnected = status?.connected || status?.state === "open";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <MessageSquare className="w-6 h-6 text-[var(--accent)]" />
          WhatsApp
        </h1>
        <p className="text-[var(--text-secondary)] text-sm">
          Conexao e configuracao do WhatsApp
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connection Status */}
        <div className="card space-y-4">
          <h2 className="font-semibold flex items-center gap-2">
            {isConnected ? (
              <Wifi className="w-4 h-4 text-green-400" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-400" />
            )}
            Status da Conexao
          </h2>

          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-400" : "bg-red-400"}`} />
            <span className="text-sm">
              {loading ? "Verificando..." : isConnected ? "Conectado" : "Desconectado"}
            </span>
          </div>

          <div className="flex gap-3">
            {!isConnected ? (
              <button onClick={handleConnect} disabled={connecting} className="btn btn-primary">
                {connecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <QrCode className="w-4 h-4" />}
                {connecting ? "Gerando QR..." : "Conectar"}
              </button>
            ) : (
              <button onClick={handleDisconnect} className="btn btn-danger">
                <WifiOff className="w-4 h-4" />
                Desconectar
              </button>
            )}
          </div>

          {/* QR Code */}
          {qrData?.qrcode && (
            <div className="bg-white rounded-lg p-4 inline-block">
              <img
                src={qrData.qrcode.startsWith("data:") ? qrData.qrcode : `data:image/png;base64,${qrData.qrcode}`}
                alt="QR Code WhatsApp"
                className="w-64 h-64"
              />
            </div>
          )}
        </div>

        {/* Webhook Config */}
        <div className="card space-y-4">
          <h2 className="font-semibold flex items-center gap-2">
            <Link className="w-4 h-4 text-[var(--accent)]" />
            Webhook
          </h2>
          <p className="text-sm text-[var(--text-secondary)]">
            URL que o UAZAPI vai chamar quando receber mensagens
          </p>

          <div className="flex gap-3">
            <input
              type="url"
              className="input flex-1"
              placeholder="https://seu-dominio.vercel.app/api/whatsapp/webhook"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
            />
            <button onClick={handleWebhookConfig} className="btn btn-primary">
              Salvar
            </button>
          </div>
        </div>
      </div>

      {/* Whitelist */}
      <div className="card space-y-4">
        <h2 className="font-semibold flex items-center gap-2">
          <Shield className="w-4 h-4 text-[var(--accent)]" />
          Numeros Autorizados (Whitelist)
        </h2>
        <p className="text-sm text-[var(--text-secondary)]">
          Somente estes numeros podem interagir com o Jarvis
        </p>

        {/* Add number */}
        <div className="flex gap-3">
          <input
            type="text"
            className="input w-48"
            placeholder="5531999999999"
            value={newPhone}
            onChange={(e) => setNewPhone(e.target.value)}
          />
          <input
            type="text"
            className="input w-48"
            placeholder="Nome (opcional)"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <button onClick={handleAddNumber} className="btn btn-primary">
            <Plus className="w-4 h-4" />
            Adicionar
          </button>
        </div>

        {/* Numbers list */}
        <div className="space-y-2">
          {whitelist.length === 0 ? (
            <p className="text-sm text-[var(--text-secondary)]">Nenhum numero cadastrado</p>
          ) : (
            whitelist.map((num: any) => (
              <div
                key={num.id}
                className="flex items-center justify-between bg-[var(--bg-secondary)] rounded-lg px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${num.is_active ? "bg-green-400" : "bg-gray-400"}`} />
                  <span className="font-mono text-sm">{num.phone_number}</span>
                  {num.name && <span className="text-[var(--text-secondary)] text-sm">({num.name})</span>}
                </div>
                <button
                  onClick={() => handleRemoveNumber(num.phone_number)}
                  className="text-red-400 hover:text-red-300 p-1"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
