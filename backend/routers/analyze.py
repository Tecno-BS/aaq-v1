from typing import List, Dict, Any, Optional, Tuple
import json
import io
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pypdf import PdfReader

import config
from models.analysis import Analysis as AnalysisDoc
from services.openai_service import analyze_slides

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
    """
    Lee cada archivo UNA SOLA VEZ y devuelve lista de (filename, content_type, data).
    Valida tipo MIME y tamaño.
    """
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


def to_image_blocks(
    file_tuples: List[Tuple[str, str, bytes]],
) -> List[Dict[str, Any]]:
    """Convierte bytes ya leídos en bloques input_image para el modelo."""
    return [
        {"type": "input_image", "image_url": config.to_data_url(ct, data)}
        for _, ct, data in file_tuples
    ]


async def read_pdf(pdf_file: UploadFile) -> Tuple[str, bytes]:
    """Lee el PDF UNA SOLA VEZ. Devuelve (texto_extraído, bytes_raw)."""
    data = await pdf_file.read()
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"El PDF supera el tamaño máximo permitido ({MAX_PDF_BYTES} bytes).",
        )
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(p.strip() for p in pages if p.strip())
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
    """
    Guarda todos los archivos en disco.
    Devuelve (slide_paths, context_paths, pdf_path) relativos a UPLOADS_DIR.
    """
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
    project_id: str = Form(...),
    contexto_json: str = Form(...),
    images: List[UploadFile] = File(...),
    context_images: List[UploadFile] = File(None),
    study_pdf: Optional[UploadFile] = File(None),
):
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="Sin API KEY de OpenAI configurada.")

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

    # 2. Leer todos los archivos UNA SOLA VEZ
    slide_tuples = await read_images(images, prefix="slide")
    context_tuples = await read_images(context_images or [], prefix="contexto")

    pdf_text: Optional[str] = None
    pdf_bytes: Optional[bytes] = None
    pdf_filename: Optional[str] = None
    if study_pdf and study_pdf.filename:
        pdf_text, pdf_bytes = await read_pdf(study_pdf)
        pdf_filename = study_pdf.filename

    # 3. Guardar archivos en disco
    analysis_id = str(uuid.uuid4())
    analysis_dir = UPLOADS_DIR / project_id / analysis_id
    slide_paths, context_paths, pdf_path = save_files(
        analysis_dir, slide_tuples, context_tuples, pdf_filename, pdf_bytes
    )

    # 4. Construir bloques para el modelo (usa los bytes ya leídos)
    context_blocks = to_image_blocks(context_tuples)
    slide_blocks = to_image_blocks(slide_tuples)
    all_image_blocks = context_blocks + slide_blocks

    # 5. Llamar al modelo
    try:
        output_text = analyze_slides(
            contexto=contexto,
            image_blocks=all_image_blocks,
            pdf_text=pdf_text,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al llamado del modelo: {e}")

    # 6. Guardar análisis en MongoDB
    analysis_doc = AnalysisDoc(
        project_id=project_id,
        answers=contexto,
        has_previous_study=contexto.get("q10", ""),
        slide_paths=slide_paths,
        context_image_paths=context_paths,
        pdf_path=pdf_path,
        output_text=output_text,
    )
    await analysis_doc.insert()

    return {"output_text": output_text, "analysis_id": str(analysis_doc.id)}
