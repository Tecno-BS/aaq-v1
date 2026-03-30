from typing import List, Dict, Any, Optional, Tuple
import json
import io
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pypdf import PdfReader

import config
from models.analysis import Analysis as AnalysisDoc
from services.analysis_graph import analysis_pipeline

router = APIRouter()

MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


@router.get("/health")
def health():
    return {"status": "ok"}


# ── Helpers ────────────────────────────────────────────────────────────────

async def read_images(
    files: List[UploadFile],
    prefix: str,
) -> List[Tuple[str, str, bytes]]:
    results = []
    for idx, f in enumerate(files, start=1):
        if f.content_type not in config.ALLOWED_MIME:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no permitido en {prefix} {idx}: {f.content_type}",
            )
        data = await f.read()
        if len(data) > config.MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"Imagen de {prefix} {idx} supera el tamaño máximo ({config.MAX_IMAGE_BYTES} bytes).",
            )
        results.append((f.filename or f"file_{idx}", f.content_type, data))
    return results


async def read_pdf(pdf_file: UploadFile) -> Tuple[str, bytes]:
    data = await pdf_file.read()
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"El PDF supera el tamaño máximo permitido ({MAX_PDF_BYTES} bytes).",
        )
    try:
        reader = PdfReader(io.BytesIO(data))
        pages  = [page.extract_text() or "" for page in reader.pages]
        text   = "\n\n".join(p.strip() for p in pages if p.strip())
        return text or "(El PDF no contiene texto extraíble.)", data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el PDF: {e}")


def save_files(
    analysis_dir: Path,
    slide_tuples: List[Tuple[str, str, bytes]],
    context_tuples: List[Tuple[str, str, bytes]],
    pdf_filename: Optional[str],
    pdf_bytes: Optional[bytes],
) -> Tuple[List[str], List[str], Optional[str]]:
    analysis_dir.mkdir(parents=True, exist_ok=True)

    slide_paths = []
    for idx, (filename, _, data) in enumerate(slide_tuples, start=1):
        dest = analysis_dir / f"slide_{idx:02d}_{filename}"
        dest.write_bytes(data)
        slide_paths.append(str(dest.relative_to(UPLOADS_DIR)))

    context_paths = []
    for idx, (filename, _, data) in enumerate(context_tuples, start=1):
        dest = analysis_dir / f"ctx_{idx:02d}_{filename}"
        dest.write_bytes(data)
        context_paths.append(str(dest.relative_to(UPLOADS_DIR)))

    pdf_path = None
    if pdf_filename and pdf_bytes:
        dest = analysis_dir / f"study_{pdf_filename}"
        dest.write_bytes(pdf_bytes)
        pdf_path = str(dest.relative_to(UPLOADS_DIR))

    return slide_paths, context_paths, pdf_path


# ── Endpoint principal ─────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze(
    project_id:    str  = Form(...),
    contexto_json: str  = Form(...),
    provider:      str  = Form(None),        # "openai" | "gemini" | None → usa el default
    openai_model:  str  = Form(None),        # "gpt-4.1" | "gpt-4o" | "gpt-5" | None → usa OPENAI_MODEL
    gemini_model:  str  = Form(None),        # "gemini-2.5-pro" | "gemini-3-pro-preview" | None → usa GEMINI_MODEL
    images:        List[UploadFile] = File(...),
    context_images: List[UploadFile] = File(None),
    study_pdf:     Optional[UploadFile] = File(None),
):
    # Resolver proveedor activo
    active_provider = (provider or config.ACTIVE_LLM_PROVIDER).lower().strip()

    # Validar que las credenciales del proveedor estén disponibles
    if active_provider == "gemini":
        if not config.GOOGLE_CREDENTIALS_PATH or not config.VERTEX_AI_PROJECT:
            raise HTTPException(
                status_code=500,
                detail="Credenciales de Gemini no configuradas. "
                       "Revisa GOOGLE_APPLICATION_CREDENTIALS y VERTEX_AI_PROJECT en backend/.env",
            )
    else:
        if not config.OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY no configurada en backend/.env")

    # 1. Parsear y validar contexto
    try:
        contexto: Dict[str, str] = json.loads(contexto_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="El campo 'contexto_json' no es un JSON válido.")

    required_keys = [f"q{i}" for i in range(11)]
    missing = [k for k in required_keys if not (contexto.get(k) or "").strip()]
    if missing:
        raise HTTPException(status_code=400, detail=f"Faltan respuestas en: {', '.join(missing)}.")

    if not images:
        raise HTTPException(status_code=400, detail="Debes adjuntar al menos 1 imagen de slides.")

    # 2. Leer todos los archivos
    slide_tuples   = await read_images(images, prefix="slide")
    context_tuples = await read_images(context_images or [], prefix="contexto")

    pdf_text:     Optional[str]   = None
    pdf_bytes:    Optional[bytes] = None
    pdf_filename: Optional[str]   = None
    if study_pdf and study_pdf.filename:
        pdf_text, pdf_bytes = await read_pdf(study_pdf)
        pdf_filename = study_pdf.filename

    # 3. Guardar archivos en disco
    analysis_id  = str(uuid.uuid4())
    analysis_dir = UPLOADS_DIR / project_id / analysis_id
    slide_paths, context_paths, pdf_path = save_files(
        analysis_dir, slide_tuples, context_tuples, pdf_filename, pdf_bytes
    )

    # 4. Convertir imágenes a data URLs para el grafo
    slide_data_urls   = [config.to_data_url(ct, d) for _, ct, d in slide_tuples]
    context_data_urls = [config.to_data_url(ct, d) for _, ct, d in context_tuples]

    # 5. Ejecutar el pipeline LangGraph
    try:
        result = analysis_pipeline.invoke({
            "provider":          active_provider,
            "openai_model":      openai_model or None,
            "gemini_model":      gemini_model or None,
            "contexto":          contexto,
            "slide_data_urls":   slide_data_urls,
            "context_data_urls": context_data_urls,
            "pdf_text":          pdf_text,
            "slide_titles":      [],
            "output_text":       "",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el pipeline de análisis: {e}")

    output_text  = result["output_text"]
    slide_titles = result["slide_titles"]

    # 6. Guardar análisis en MongoDB
    analysis_doc = AnalysisDoc(
        project_id=project_id,
        answers=contexto,
        has_previous_study=contexto.get("q10", ""),
        slide_paths=slide_paths,
        slide_titles=slide_titles,
        context_image_paths=context_paths,
        pdf_path=pdf_path,
        output_text=output_text,
    )
    await analysis_doc.insert()

    return {
        "output_text":  output_text,
        "analysis_id":  str(analysis_doc.id),
        "slide_titles": slide_titles,
        "provider":     active_provider,
        "model":        (gemini_model or config.GEMINI_MODEL) if active_provider == "gemini" else (openai_model or config.OPENAI_MODEL),
    }
