"""
Factory de modelos LangChain.
Devuelve un BaseChatModel según el proveedor solicitado.
"""

from __future__ import annotations

import config
from langchain_core.language_models.chat_models import BaseChatModel


def get_llm(provider: str | None = None, model: str | None = None) -> BaseChatModel:
    """
    Devuelve el modelo LangChain correspondiente al proveedor.
    Si provider es None, usa config.ACTIVE_LLM_PROVIDER.
    Si model es None, usa el modelo por defecto del proveedor (config.OPENAI_MODEL o config.GEMINI_MODEL).

    Proveedores soportados:
      - "openai"  → ChatOpenAI  (GPT-4o o el modelo en OPENAI_MODEL)
      - "gemini"  → ChatVertexAI (Gemini via Vertex AI GCP)
    """
    provider = (provider or config.ACTIVE_LLM_PROVIDER).lower().strip()

    if provider == "gemini":
        return _build_gemini(model=model)

    return _build_openai(model=model)


# ─── Builders internos ────────────────────────────────────────────────────────

def _build_openai(model: str | None = None) -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    if not config.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY no está configurada. "
            "Agrégala al archivo backend/.env"
        )
    return ChatOpenAI(
        model=model or config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0,
    )


def _build_gemini(model: str | None = None) -> BaseChatModel:
    from langchain_google_vertexai import ChatVertexAI
    from google.oauth2.service_account import Credentials

    if not config.GOOGLE_CREDENTIALS_PATH:
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS no está configurada. "
            "Agrégala al archivo backend/.env apuntando al JSON de la service account."
        )
    if not config.VERTEX_AI_PROJECT:
        raise RuntimeError(
            "VERTEX_AI_PROJECT no está configurado. "
            "Agrégalo al archivo backend/.env con el ID de tu proyecto GCP."
        )

    credentials = Credentials.from_service_account_file(
        config.GOOGLE_CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return ChatVertexAI(
        model=model or config.GEMINI_MODEL,
        project=config.VERTEX_AI_PROJECT,
        credentials=credentials,
        temperature=0,
    )
