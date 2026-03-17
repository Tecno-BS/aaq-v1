import json
import re
from typing import List, Dict, Any, Optional

import config

QUESTION_TEXTS = {
    "q0":  "0. ¿Cuál es el perfil o rol que debo adoptar?",
    "q1":  "1. ¿Cuáles son los antecedentes del proyecto? (categoría, cliente, problema de investigación, etc.)",
    "q2":  "2. ¿Cuál es la pregunta de negocio o hipótesis a validar?",
    "q3":  "3. ¿Qué tipo de estudio es? (prueba de producto, comunicación, salud de marca, exploratorio, satisfacción, fidelización, etc.)",
    "q4":  "4. ¿Cuáles son los propósitos estratégicos? (¿Qué espera hacer el cliente con los resultados?)",
    "q5":  "5. ¿Qué segmentos y variables se evalúan?",
    "q6":  "6. ¿Cuál es la muestra y el margen de error?",
    "q7":  "7. ¿Desde qué margen de error se considera un cambio significativo?",
    "q8":  "8. ¿Qué modelos de análisis se usan? (Describa brevemente.)",
    "q9":  "9. ¿Se trata de una o varias mediciones?",
    "q10": "10. ¿Existe un estudio cualitativo anterior?",
}

QUESTION_ORDER = ["q0","q1","q2","q3","q4","q5","q6","q7","q8","q9","q10"]


# ─── Extracción de títulos de slides ─────────────────────────────────────────

def extract_slide_titles(slide_blocks: List[Dict[str, Any]]) -> List[str]:
    """
    Llama al modelo para identificar el título principal de cada diapositiva.
    Devuelve lista de títulos en el mismo orden que slide_blocks.
    Si falla o el JSON es inválido, devuelve ["Slide 1", "Slide 2", ...].
    """
    n = len(slide_blocks)
    fallback = [f"Slide {i + 1}" for i in range(n)]

    if n == 0:
        return []

    try:
        prompt = (
            f"Se te muestran {n} diapositiva(s). "
            "Identifica el título o encabezado principal de cada una, "
            "en el mismo orden en que aparecen. "
            "Responde ÚNICAMENTE con un array JSON válido de strings, sin explicación ni código. "
            f'Ejemplo para {n} slides: '
            + json.dumps([f"Título de la diapositiva {i+1}" for i in range(min(n, 3))]) +
            ". Si una diapositiva no tiene título visible, describe su contenido en máximo 6 palabras."
        )

        content = [*slide_blocks, {"type": "input_text", "text": prompt}]

        resp = config.client.responses.create(
            model=config.OPENAI_MODEL,
            instructions=(
                "Eres un extractor de títulos de diapositivas. "
                "Responde siempre con un array JSON de strings y nada más."
            ),
            input=[{"role": "user", "content": content}],
        )

        raw = resp.output_text.strip()
        # Quitar posibles bloques de código markdown
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        titles = json.loads(raw)

        if not isinstance(titles, list):
            return fallback

        # Ajustar longitud si el modelo devuelve más o menos
        result = [str(t).strip() for t in titles[:n]]
        while len(result) < n:
            result.append(f"Slide {len(result) + 1}")
        return result

    except Exception:
        return fallback


# ─── Construcción del prompt principal ───────────────────────────────────────

def build_user_text(
    contexto: Dict[str, str],
    pdf_text: Optional[str],
    slide_titles: Optional[List[str]] = None,
) -> str:
    partes = []
    for qid in QUESTION_ORDER:
        pregunta = QUESTION_TEXTS.get(qid, qid)
        respuesta = (contexto.get(qid) or "").strip()
        partes.append(f"{pregunta}\n{respuesta}")

    contexto_formateado = "\n\n".join(partes)

    pdf_section = ""
    if pdf_text:
        pdf_section = (
            "\n\n--- CONTENIDO DEL ESTUDIO CUALITATIVO PREVIO (PDF) ---\n"
            f"{pdf_text}\n"
            "--- FIN DEL ESTUDIO CUALITATIVO ---"
        )

    # Inyectar índice de slides con sus títulos identificados
    slides_section = ""
    if slide_titles:
        slides_list = "\n".join(
            f"  - Slide {i + 1}: \"{t}\"" for i, t in enumerate(slide_titles)
        )
        slides_section = (
            "\n\nÍNDICE DE DIAPOSITIVAS (en orden de aparición):\n"
            f"{slides_list}"
        )

    # Instrucción de salida ajustada para usar nombres de slides
    slide_ref = (
        "el TÍTULO EXACTO de la diapositiva según el índice anterior (no 'Slide N')"
        if slide_titles
        else "'Slide 1', 'Slide 2', etc. en el mismo orden de las imágenes"
    )

    return (
        "Responde SIEMPRE en español.\n\n"
        "A continuación va el CONTEXTO (respuestas 0–10) ya diligenciado:\n"
        "----\n"
        f"{contexto_formateado}"
        f"{pdf_section}"
        f"{slides_section}\n"
        "----\n\n"
        "INSTRUCCIONES DE SALIDA:\n"
        f"- Entrega una tabla (markdown) con 2 columnas: 'Gráfica' y 'Análisis explicativo'.\n"
        f"- En 'Gráfica', usa {slide_ref}.\n"
        "- Luego: resumen ejecutivo (3 hallazgos clave).\n"
        "- Luego: tabla ejecutiva de recomendaciones (por slide y generales).\n"
    )


def analyze_slides(
    contexto: Dict[str, str],
    image_blocks: List[Dict[str, Any]],
    pdf_text: Optional[str] = None,
    slide_titles: Optional[List[str]] = None,
) -> str:
    user_text = build_user_text(contexto, pdf_text, slide_titles)
    content = [{"type": "input_text", "text": user_text}, *image_blocks]

    resp = config.client.responses.create(
        model=config.OPENAI_MODEL,
        instructions=config.SYSTEM_INSTRUCTIONS,
        input=[{"role": "user", "content": content}],
    )

    return resp.output_text
