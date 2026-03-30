import os
import base64
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# ─── OpenAI ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o")

# ─── Google / Vertex AI ───────────────────────────────────────────────────────
GEMINI_MODEL              = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-001")
VERTEX_AI_PROJECT         = os.getenv("VERTEX_AI_PROJECT", "")
GOOGLE_CREDENTIALS_PATH   = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

# ─── Proveedor activo por defecto ─────────────────────────────────────────────
ACTIVE_LLM_PROVIDER = os.getenv("ACTIVE_LLM_PROVIDER", "openai")  # "openai" | "gemini"

# ─── Prompts del sistema ──────────────────────────────────────────────────────
PROMPTS_DIR         = BASE_DIR / "prompts"
SYSTEM_INSTRUCTIONS = (PROMPTS_DIR / "base.md").read_text(encoding="utf-8")   # fallback


def get_system_instructions(provider: str) -> str:
    """
    Devuelve el prompt de sistema para el proveedor indicado.
    Busca prompts/{provider}.md; si no existe, usa prompts/base.md como fallback.
    """
    provider_path = PROMPTS_DIR / f"{provider.lower().strip()}.md"
    if provider_path.exists():
        return provider_path.read_text(encoding="utf-8")
    return SYSTEM_INSTRUCTIONS

# ─── Límites de archivos ──────────────────────────────────────────────────────
MAX_IMAGE_BYTES = 7 * 1024 * 1024   # 7 MB por imagen
ALLOWED_MIME    = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


def to_data_url(content_type: str, data: bytes) -> str:
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{content_type};base64,{b64}"
