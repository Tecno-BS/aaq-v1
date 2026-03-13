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


def build_user_text(contexto: Dict[str, str], pdf_text: Optional[str]) -> str:
    partes = []
    for qid in QUESTION_ORDER:
        pregunta = QUESTION_TEXTS.get(qid, qid)
        respuesta = (contexto.get(qid) or "").strip()
        partes.append(f"{pregunta}\n{respuesta}")

    contexto_formateado = "\n\n".join(partes)

    # Añadir contenido del PDF al bloque de q10 si existe
    pdf_section = ""
    if pdf_text:
        pdf_section = (
            "\n\n--- CONTENIDO DEL ESTUDIO CUALITATIVO PREVIO (PDF) ---\n"
            f"{pdf_text}\n"
            "--- FIN DEL ESTUDIO CUALITATIVO ---"
        )

    return (
        "Responde SIEMPRE en español.\n\n"
        "A continuación va el CONTEXTO (respuestas 0–10) ya diligenciado:\n"
        "----\n"
        f"{contexto_formateado}"
        f"{pdf_section}\n"
        "----\n\n"
        "INSTRUCCIONES DE SALIDA:\n"
        "- Entrega una tabla (markdown) con 2 columnas: 'Gráfica' y 'Análisis explicativo'.\n"
        "- En 'Gráfica', usa 'Slide 1', 'Slide 2', etc. en el mismo orden de las imágenes.\n"
        "- Luego: resumen ejecutivo (3 hallazgos clave).\n"
        "- Luego: tabla ejecutiva de recomendaciones (por slide y generales).\n"
    )


def analyze_slides(
    contexto: Dict[str, str],
    image_blocks: List[Dict[str, Any]],
    pdf_text: Optional[str] = None,
) -> str:
    user_text = build_user_text(contexto, pdf_text)
    content = [{"type": "input_text", "text": user_text}, *image_blocks]

    resp = config.client.responses.create(
        model=config.OPENAI_MODEL,
        instructions=config.SYSTEM_INSTRUCTIONS,
        input=[{"role": "user", "content": content}],
    )

    return resp.output_text
