# AAQ-BS — Análisis cuantitativo a partir de slides

## Estructura

- `backend/`: API FastAPI que recibe:
  - `contexto` (texto con respuestas 0–10).
  - `images` (lista de imágenes PNG/JPG/WebP).
  Llama a OpenAI (modelo multimodal) y devuelve `output_text` en markdown.

- `frontend/`: SPA en React + Vite.
  - Formulario para pegar el contexto.
  - Uploader de imágenes.
  - Llama a `POST /analyze` del backend y muestra el markdown devuelto.

## Requisitos

- Python 3.10+ (recomendado)
- Node.js 20+
- Cuenta y API key de OpenAI

## Backend

```bash
cd backend

# Crear entorno virtual (opcional si ya tienes .venv)
python -m venv .venv
.\.venv\Scripts\activate  # En Windows PowerShell

# Instalar dependencias
pip install -r requirements.txt

# Variables de entorno (.env)
# Crea un archivo .env en backend/ con al menos:
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-5.2