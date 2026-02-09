"""
Jarvis - Configuracoes centralizadas
Carrega todas as variaveis de ambiente necessarias.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Gemini AI ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# --- WhatsApp (UAZAPI) ---
UAZAPI_BASE_URL = os.getenv("UAZAPI_BASE_URL", "https://atendsoft.uazapi.com")
UAZAPI_ADMIN_TOKEN = os.getenv("UAZAPI_ADMIN_TOKEN", "")
UAZAPI_INSTANCE_TOKEN = os.getenv("UAZAPI_INSTANCE_TOKEN", "")
ALLOWED_PHONE = os.getenv("ALLOWED_PHONE", "")

# --- Jules API ---
JULES_API_KEY = os.getenv("JULES_API_KEY", "")
JULES_API_URL = "https://jules.googleapis.com/v1alpha"

# --- GitHub ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "josepedro15")

# --- Vercel ---
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")

# --- N8N (READ ONLY) ---
N8N_API_KEY = os.getenv("N8N_API_KEY", "")
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "")

# --- Supabase ---
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
