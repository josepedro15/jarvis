"""
Jarvis - Cliente Gemini 2.5 Flash
Gerencia a comunicacao com a API do Gemini para IA conversacional.
"""
import google.generativeai as genai
import json
from .config import GOOGLE_API_KEY
from . import supabase_client as db

# Configurar SDK
genai.configure(api_key=GOOGLE_API_KEY)


def get_model(model_name: str = None, temperature: float = None):
    """Cria instancia do modelo Gemini com config do banco."""
    config = db.get_ai_config()
    model = model_name or config.get("model", "gemini-2.5-flash")
    temp = temperature if temperature is not None else config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 2048)

    return genai.GenerativeModel(
        model_name=model,
        generation_config=genai.GenerationConfig(
            temperature=temp,
            max_output_tokens=max_tokens,
        )
    )


def build_chat_history(phone: str, system_prompt: str = None) -> list:
    """Constroi historico de chat para o Gemini a partir do banco."""
    # Buscar config da IA
    config = db.get_ai_config()
    prompt = system_prompt or config.get("system_prompt", "")

    # Buscar historico recente
    history = db.get_conversation_history(phone, limit=20)

    # Montar historico no formato do Gemini
    chat_history = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        chat_history.append({"role": role, "parts": [msg["content"]]})

    return prompt, chat_history


async def chat(phone: str, user_message: str, extra_context: str = "") -> str:
    """
    Processa mensagem do usuario e retorna resposta do Gemini.
    Salva tanto a mensagem do usuario quanto a resposta no historico.
    """
    try:
        # Salvar mensagem do usuario
        db.save_message(phone, "user", user_message)

        # Buscar estado da conversa
        state = db.get_conversation_state(phone)
        current_state = state.get("current_state", "idle")
        state_data = state.get("state_data", {})

        # Construir contexto
        system_prompt, chat_history = build_chat_history(phone)

        # Adicionar contexto extra (estado da conversa, repos disponiveis, etc.)
        context_parts = []
        if extra_context:
            context_parts.append(extra_context)
        if current_state != "idle":
            context_parts.append(f"[Estado atual da conversa: {current_state}]")
            if state_data:
                context_parts.append(f"[Dados do estado: {json.dumps(state_data, ensure_ascii=False)}]")

        # Montar prompt completo
        full_system = system_prompt
        if context_parts:
            full_system += "\n\nContexto atual:\n" + "\n".join(context_parts)

        # Criar modelo e chat
        model = get_model()
        chat_session = model.start_chat(history=chat_history)

        # Enviar mensagem com system prompt como instrucao
        full_message = user_message
        if not chat_history:
            # Primeira mensagem - incluir system prompt
            full_message = f"[System: {full_system}]\n\nUsuario: {user_message}"

        response = chat_session.send_message(full_message)
        response_text = response.text

        # Salvar resposta no historico
        db.save_message(phone, "assistant", response_text)

        return response_text

    except Exception as e:
        error_msg = f"Erro no Gemini: {str(e)}"
        db.log("ai", error_msg, level="error", details={"phone": phone, "error": str(e)})
        return "Desculpe, tive um problema ao processar sua mensagem. Tente novamente."


def parse_intent(response_text: str) -> tuple[dict | None, str]:
    """
    Extrai intent JSON e texto limpo da resposta do Gemini.
    Retorna (intent_dict, clean_text)
    """
    intent = None
    clean_text = response_text

    # Tentar extrair JSON do inicio da resposta
    try:
        if response_text.strip().startswith("{"):
            # Encontrar o fim do JSON
            brace_count = 0
            json_end = -1
            for i, char in enumerate(response_text):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            if json_end > 0:
                json_str = response_text[:json_end]
                intent = json.loads(json_str)
                clean_text = response_text[json_end:].strip()
    except (json.JSONDecodeError, ValueError):
        pass

    return intent, clean_text


async def test_prompt(message: str, system_prompt: str = None) -> str:
    """Testa um prompt sem salvar no historico (para o painel admin)."""
    try:
        config = db.get_ai_config()
        prompt = system_prompt or config.get("system_prompt", "")

        model = get_model()
        response = model.generate_content(
            f"[System: {prompt}]\n\nUsuario: {message}"
        )
        return response.text
    except Exception as e:
        return f"Erro: {str(e)}"
