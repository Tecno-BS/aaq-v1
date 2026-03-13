import io
import re
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, KeepTogether,
)

router = APIRouter(tags=["export"])

# ─── Paleta Brandstrat ────────────────────────────────────────────────────────
C_ORANGE    = HexColor("#F26522")
C_NAVY      = HexColor("#1A2035")
C_ORANGE_LT = HexColor("#FEF0E7")
C_ROW_ALT   = HexColor("#F7F8FA")
C_BG        = HexColor("#F0F2F5")
C_MUTED     = HexColor("#5A6478")
C_MUTED2    = HexColor("#96A0B0")
C_BORDER    = HexColor("#E3E7ED")
C_TEXT      = HexColor("#1A2035")

FONT   = "Helvetica"
FONT_B = "Helvetica-Bold"
FONT_I = "Helvetica-Oblique"

PAGE_W, PAGE_H = A4
MARGIN_H = 2.2 * cm
MARGIN_V = 2.0 * cm
CONTENT_W = PAGE_W - 2 * MARGIN_H


# ─── Estilos ──────────────────────────────────────────────────────────────────
def _styles() -> dict:
    return {
        "h1": ParagraphStyle(
            "h1", fontName=FONT_B, fontSize=14, textColor=white,
            leading=19, leftIndent=6, spaceAfter=0, spaceBefore=0,
        ),
        "h2": ParagraphStyle(
            "h2", fontName=FONT_B, fontSize=12, textColor=C_NAVY,
            leading=17, leftIndent=10, spaceAfter=0, spaceBefore=0,
        ),
        "h3": ParagraphStyle(
            "h3", fontName=FONT_B, fontSize=10.5, textColor=C_MUTED,
            leading=15, spaceBefore=6, spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body", fontName=FONT, fontSize=10, textColor=C_TEXT,
            leading=15, spaceBefore=2, spaceAfter=3, alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName=FONT, fontSize=10, textColor=C_TEXT,
            leading=15, spaceBefore=1, spaceAfter=2,
            leftIndent=18, firstLineIndent=0,
        ),
        "th": ParagraphStyle(
            "th", fontName=FONT_B, fontSize=9, textColor=white,
            leading=12, alignment=TA_CENTER,
        ),
        "td": ParagraphStyle(
            "td", fontName=FONT, fontSize=9, textColor=C_TEXT,
            leading=12, alignment=TA_LEFT,
        ),
        "footer": ParagraphStyle(
            "footer", fontName=FONT_I, fontSize=7.5, textColor=C_MUTED2,
            alignment=TA_CENTER,
        ),
        "date": ParagraphStyle(
            "date", fontName=FONT_I, fontSize=8, textColor=C_MUTED2,
            alignment=TA_RIGHT,
        ),
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _md(text: str) -> str:
    """Convierte markdown inline básico a markup de ReportLab."""
    # Escapar & y < que no son parte de etiquetas
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    return text


def _table_flowable(table_lines: list[str], st: dict) -> Table | None:
    """Parsea un bloque de tabla markdown y devuelve un Table de reportlab."""
    rows = []
    for line in table_lines:
        # Saltar fila separadora (|---|---|)
        if re.match(r"^\|[\s\-:]+\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)

    if not rows:
        return None

    num_cols = max(len(r) for r in rows)
    col_w = CONTENT_W / num_cols

    formatted = []
    for i, row in enumerate(rows):
        # Rellenar celdas faltantes
        row = row + [""] * (num_cols - len(row))
        style = st["th"] if i == 0 else st["td"]
        formatted.append([Paragraph(_md(c), style) for c in row])

    tbl = Table(formatted, colWidths=[col_w] * num_cols, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  C_ORANGE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, C_ROW_ALT]),
        ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.2, C_ORANGE),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl


def _h1_block(text: str, st: dict) -> Table:
    """Título H1 en caja naranja de ancho completo."""
    data = [[Paragraph(_md(text), st["h1"])]]
    tbl = Table(data, colWidths=[CONTENT_W])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_ORANGE),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    return tbl


def _h2_block(text: str, st: dict) -> Table:
    """H2 con barra naranja a la izquierda y fondo naranja suave."""
    data = [["", Paragraph(_md(text), st["h2"])]]
    tbl = Table(data, colWidths=[4, CONTENT_W - 4])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1),  C_ORANGE),
        ("BACKGROUND",    (1, 0), (1, -1),  C_ORANGE_LT),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (0, -1),  0),
        ("RIGHTPADDING",  (0, 0), (0, -1),  0),
        ("LEFTPADDING",   (1, 0), (1, -1),  10),
        ("RIGHTPADDING",  (1, 0), (1, -1),  8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl


def _page_decoration(canvas, doc):
    """Línea naranja en el margen superior + número de página abajo."""
    canvas.saveState()
    # Línea superior naranja
    canvas.setStrokeColor(C_ORANGE)
    canvas.setLineWidth(2.5)
    canvas.line(MARGIN_H, PAGE_H - 0.7 * cm, PAGE_W - MARGIN_H, PAGE_H - 0.7 * cm)
    # Número de página
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(C_MUTED2)
    canvas.drawCentredString(PAGE_W / 2, 0.6 * cm, f"Página {doc.page}")
    canvas.restoreState()


# ─── Constructor del documento ────────────────────────────────────────────────
def _build_story(output_text: str, project_name: str, project_code: str) -> list:
    st = _styles()
    story = []

    # ── Encabezado de marca ───────────────────────────────────────────────────
    brand_data = [[
        Paragraph(
            "BRANDSTRAT  <font color='#F26522'>·</font>  "
            "AAQ — Análisis cuantitativo",
            ParagraphStyle(
                "brand", fontName=FONT_B, fontSize=13,
                textColor=white, leading=18,
            ),
        )
    ]]
    brand_tbl = Table(brand_data, colWidths=[CONTENT_W])
    brand_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 13),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 13),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
    ]))
    story.append(brand_tbl)
    story.append(Spacer(1, 3))

    # ── Franja naranja con nombre del proyecto ────────────────────────────────
    proj_val = f"[{project_code}]  {project_name}" if project_code else project_name
    proj_data = [[
        Paragraph(
            proj_val,
            ParagraphStyle(
                "proj", fontName=FONT_B, fontSize=11,
                textColor=white, leading=16,
            ),
        )
    ]]
    proj_tbl = Table(proj_data, colWidths=[CONTENT_W])
    proj_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_ORANGE),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
    ]))
    story.append(proj_tbl)
    story.append(Spacer(1, 5))

    # Fecha
    fecha = datetime.now().strftime("%d/%m/%Y  %H:%M")
    story.append(Paragraph(f"Generado el {fecha}", st["date"]))
    story.append(Spacer(1, 14))

    # ── Contenido ─────────────────────────────────────────────────────────────
    lines = output_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Tabla markdown
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            tbl = _table_flowable(table_lines, st)
            if tbl:
                story.append(Spacer(1, 6))
                story.append(tbl)
                story.append(Spacer(1, 8))
            continue

        # Línea vacía
        if not line:
            story.append(Spacer(1, 5))
            i += 1
            continue

        # H1
        if re.match(r"^# ", line):
            blk = _h1_block(line[2:].strip(), st)
            story.append(Spacer(1, 8))
            story.append(KeepTogether([blk, Spacer(1, 6)]))

        # H2
        elif re.match(r"^## ", line):
            blk = _h2_block(line[3:].strip(), st)
            story.append(Spacer(1, 8))
            story.append(KeepTogether([blk, Spacer(1, 4)]))

        # H3
        elif re.match(r"^### ", line):
            story.append(Paragraph(_md(line[4:].strip()), st["h3"]))

        # Bullet
        elif re.match(r"^[-*•]\s", line):
            text = _md(re.sub(r"^[-*•]\s+", "", line))
            story.append(Paragraph(f"•  {text}", st["bullet"]))

        # Texto normal
        else:
            story.append(Paragraph(_md(line), st["body"]))

        i += 1

    # ── Pie ───────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width=CONTENT_W, thickness=0.4, color=C_BORDER))
    story.append(Spacer(1, 5))
    story.append(
        Paragraph(
            "© Brandstrat · Documento generado automáticamente por AAQ",
            st["footer"],
        )
    )
    return story


# ─── Endpoint ─────────────────────────────────────────────────────────────────
class ExportBody(BaseModel):
    output_text: str
    project_name: str = "Análisis"
    project_code: str = ""


@router.post("/export-pdf")
async def export_pdf(body: ExportBody):
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_V,
        bottomMargin=MARGIN_V + 0.4 * cm,
        title=body.project_name,
        author="Brandstrat · AAQ",
    )

    story = _build_story(body.output_text, body.project_name, body.project_code)
    doc.build(story, onFirstPage=_page_decoration, onLaterPages=_page_decoration)

    buf.seek(0)
    safe_name = re.sub(r"[^\w\-]", "_", body.project_name)[:40]
    filename = f"analisis_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
