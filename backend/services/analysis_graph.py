"""
Pipeline de análisis construido con LangGraph.

Grafo:
  START → extract_titles_node → analyze_node → END

Ambos nodos son agnósticos al proveedor: obtienen su modelo llamando
a get_llm(state["provider"]), que devuelve ChatOpenAI o ChatVertexAI
con la misma interfaz LangChain.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

import config
from services.providers import get_llm
from services.openai_service import build_user_text


# ─── Estado del grafo ─────────────────────────────────────────────────────────

class AnalysisState(TypedDict):
    provider: str                       # "openai" | "gemini"
    openai_model: Optional[str]         # sobrescribe OPENAI_MODEL si se especifica
    gemini_model: Optional[str]         # sobrescribe GEMINI_MODEL si se especifica
    contexto: Dict[str, str]            # q0–q10
    slide_data_urls: List[str]          # data:image/png;base64,...
    context_data_urls: List[str]        # imágenes de contexto
    pdf_text: Optional[str]             # texto extraído del PDF cualitativo
    slide_titles: List[str]             # llenado por extract_titles_node
    output_text: str                    # llenado por analyze_node


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _image_block(data_url: str) -> Dict[str, Any]:
    """Convierte un data URL al formato de imagen de LangChain (funciona con OpenAI y Gemini)."""
    return {"type": "image_url", "image_url": {"url": data_url}}


def _resolve_model(state: AnalysisState) -> Optional[str]:
    """Devuelve el modelo a usar según el proveedor activo y los overrides del estado."""
    if state["provider"] == "gemini":
        return state.get("gemini_model")
    return state.get("openai_model")


# ─── Nodo 1: extraer títulos de slides ───────────────────────────────────────

def extract_titles_node(state: AnalysisState) -> Dict:
    n = len(state["slide_data_urls"])

    if n == 0:
        return {"slide_titles": []}

    llm = get_llm(state["provider"], model=_resolve_model(state))

    slide_images = [_image_block(url) for url in state["slide_data_urls"]]
    prompt_text = (
        f"Se te muestran {n} diapositiva(s). "
        "Identifica el título o encabezado principal de cada una, "
        "en el mismo orden en que aparecen. "
        "Responde ÚNICAMENTE con un array JSON válido de strings, sin explicación ni código. "
        f'Ejemplo para {n} slides: '
        + json.dumps([f"Título de la diapositiva {i + 1}" for i in range(min(n, 3))])
        + ". Si una diapositiva no tiene título visible, describe su contenido en máximo 6 palabras."
    )

    message = HumanMessage(content=[
        *slide_images,
        {"type": "text", "text": prompt_text},
    ])

    titles_instruction = (
        "Eres un extractor de títulos de diapositivas. "
        "Responde siempre con un array JSON de strings y nada más. "
        "No hagas preguntas ni agregues explicaciones."
    )
    system = SystemMessage(content=titles_instruction)

    fallback = [f"Slide {i + 1}" for i in range(n)]

    try:
        resp = llm.invoke([system, message])
        raw = resp.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        titles = json.loads(raw)

        if not isinstance(titles, list):
            return {"slide_titles": fallback}

        result = [str(t).strip() for t in titles[:n]]
        while len(result) < n:
            result.append(f"Slide {len(result) + 1}")
        return {"slide_titles": result}

    except Exception:
        return {"slide_titles": fallback}


# ─── Nodo 2: análisis principal ───────────────────────────────────────────────

def analyze_node(state: AnalysisState) -> Dict:
    llm = get_llm(state["provider"], model=_resolve_model(state))

    user_text = build_user_text(
        contexto=state["contexto"],
        pdf_text=state["pdf_text"],
        slide_titles=state["slide_titles"],
    )

    all_images = [
        _image_block(url)
        for url in (state["context_data_urls"] + state["slide_data_urls"])
    ]

    message = HumanMessage(content=[
        {"type": "text", "text": user_text},
        *all_images,
    ])

    system = SystemMessage(content=config.get_system_instructions(state["provider"]))

    resp = llm.invoke([system, message])
    return {"output_text": resp.content}


# ─── Construcción y compilación del grafo ────────────────────────────────────

_builder = StateGraph(AnalysisState)
_builder.add_node("extract_titles", extract_titles_node)
_builder.add_node("analyze", analyze_node)
_builder.set_entry_point("extract_titles")
_builder.add_edge("extract_titles", "analyze")
_builder.add_edge("analyze", END)

analysis_pipeline = _builder.compile()
