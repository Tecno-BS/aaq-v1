# AAQ-BS — Análisis cuantitativo de slides

Herramienta interna de **Brandstrat** para analizar presentaciones de estudios cuantitativos usando visión artificial (OpenAI multimodal). El analista sube las slides del reporte, diligencia un formulario de contexto y recibe un análisis detallado en texto que puede descargar como PDF con los colores corporativos.

---

## Arquitectura

```
AAQ - v0.1/
├── backend/                  # API FastAPI
│   ├── routers/
│   │   ├── analyze.py        # POST /analyze  — llama al modelo y guarda en DB
│   │   ├── projects.py       # CRUD proyectos + GET historial de análisis
│   │   └── export.py         # POST /export-pdf  — genera PDF con reportlab
│   ├── models/
│   │   ├── project.py        # Documento MongoDB: proyectos
│   │   └── analysis.py       # Documento MongoDB: análisis
│   ├── services/
│   │   └── openai_service.py # Construcción del prompt y llamada a OpenAI
│   ├── uploads/              # Archivos subidos (gitignored)
│   ├── app.py                # Entrada FastAPI + lifespan (init DB)
│   ├── database.py           # Conexión Motor / Beanie
│   ├── config.py             # Lectura de variables de entorno
│   ├── prompt.txt            # System prompt del agente
│   └── requirements.txt
└── frontend/                 # SPA React + Vite
    ├── src/
    │   ├── views/
    │   │   ├── HomeView.jsx   # Dashboard de proyectos (tarjetas)
    │   │   └── AnalysisView.jsx # Vista de análisis de tres columnas
    │   ├── components/
    │   │   ├── ContextWizard.jsx # Panel izquierdo: preguntas de contexto
    │   │   ├── ImagesPanel.jsx   # Panel central: slides, contexto, PDF
    │   │   └── ResultPanel.jsx   # Panel derecho: historial de análisis
    │   ├── services/
    │   │   └── api.js         # Funciones fetch al backend
    │   ├── constants/
    │   │   └── questions.js   # Definición de las 11 preguntas de contexto
    │   ├── App.jsx            # Shell principal + routing simple
    │   ├── App.css            # Design system Brandstrat
    │   └── index.css          # Reset global
    └── public/
        └── bs-logo-180x180.png
```

---

## Requisitos previos

| Herramienta | Versión mínima |
|---|---|
| Python | 3.10 |
| Node.js | 20 |
| MongoDB Community Server | 7.x (local) |
| API key de OpenAI | modelo multimodal (ej: `gpt-4o`) |

---

## Instalación y puesta en marcha

### 1. MongoDB

Instala [MongoDB Community Server](https://www.mongodb.com/try/download/community) y verifica que esté corriendo:

```bash
mongosh
# debe conectar a mongodb://localhost:27017
```

### 2. Backend

```bash
cd backend

# Crear entorno virtual
python -m venv .venv
.\.venv\Scripts\activate       # Windows PowerShell
# source .venv/bin/activate    # macOS / Linux

# Instalar dependencias
pip install -r requirements.txt

# Variables de entorno — crear backend/.env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
MONGODB_URI=mongodb://localhost:27017/aaq_bs

# Arrancar el servidor
uvicorn app:app --reload --port 8000
```

Docs interactivas disponibles en `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend

npm install

# Variables de entorno — crear frontend/.env.local
VITE_API_BASE_URL=http://localhost:8000

npm run dev
# Abre http://localhost:5173
```

---

## Funcionalidades

### Dashboard de proyectos
- Crear proyectos con **nombre** y **código** (ej: `BS-2026-042`).
- Tarjetas con fecha de última modificación.
- **Confirmación** antes de eliminar un proyecto (y todos sus análisis).
- Skeletons animados mientras cargan los proyectos desde MongoDB.

### Vista de análisis (tres columnas)

#### Columna izquierda — Contexto
- **11 preguntas de contexto** (Q0–Q10) collapsibles con barra de progreso.
- Las respuestas se **pre-poblan automáticamente** al entrar al proyecto con los datos del análisis más reciente.
- **Q10** (estudio cualitativo previo) es un toggle **Sí / No**. Si se responde "Sí", aparece una zona de carga de PDF en el panel central.
- Botón para limpiar el formulario sin borrar el historial.

#### Columna central — Imágenes
- **Slides del reporte** (PNG, JPG, WebP — múltiples archivos).
- **Material de contexto** (briefings, esquemas — opcional).
- **Estudio cualitativo previo en PDF** (solo si Q10 = Sí).
- **Preview al hacer clic**: lightbox con imagen a pantalla completa (cierre con Esc o clic fuera).
- Barra de progreso por pasos mientras se procesa: *Subiendo archivos → Procesando imágenes → Generando análisis → Finalizando*.

#### Columna derecha — Historial
- Lista de todos los análisis del proyecto con **versionado** (v1, v2, v3…).
- Cada tarjeta muestra: versión, fecha/hora, número de slides, imágenes de contexto y si se adjuntó PDF.
- El análisis más reciente se marca como **"Último"**.
- Botón **"PDF"** en cada tarjeta para descargar ese análisis de forma independiente.
- Skeletons de carga mientras se recupera el historial desde MongoDB.

### Exportación PDF
El endpoint `POST /export-pdf` genera un documento con:
- Encabezado navy con marca Brandstrat.
- Franja naranja con nombre y código del proyecto.
- H1 en caja naranja · H2 con barra naranja y fondo suave · H3 gris.
- Bullets con símbolo `•`.
- Tablas markdown renderizadas como tablas PDF (header naranja, filas alternas).
- Número de página y línea naranja en todas las páginas.
- Pie de página con fecha de generación.

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Backend API | FastAPI 0.115 + Uvicorn |
| ODM / Driver | Beanie 1.27 + Motor 3.7 (async MongoDB) |
| IA | OpenAI Python SDK — modelo multimodal |
| PDF | ReportLab 4.2 |
| Extracción PDF | pypdf |
| Frontend | React 18 + Vite |
| Iconos | lucide-react |
| Fuente | Inter (Google Fonts) |
| Base de datos | MongoDB (local) |

---

## Variables de entorno

### `backend/.env`

| Variable | Descripción |
|---|---|
| `OPENAI_API_KEY` | API key de OpenAI |
| `OPENAI_MODEL` | Modelo a usar (ej: `gpt-4o`) |
| `MONGODB_URI` | URI de MongoDB (ej: `mongodb://localhost:27017/aaq_bs`) |

### `frontend/.env.local`

| Variable | Descripción |
|---|---|
| `VITE_API_BASE_URL` | URL base del backend (ej: `http://localhost:8000`) |

---

## Notas de desarrollo

- Los archivos subidos se guardan en `backend/uploads/{project_id}/{analysis_id}/` y están excluidos del repositorio vía `.gitignore`.
- El frontend usa React 18 con `createRoot`. Los handlers de file input capturan el `FileList` en una variable local **antes** de resetear el input para evitar el race condition con el batching automático de React 18.
- El system prompt del agente está en `backend/prompt.txt` e incluye el catálogo de soluciones Brandstrat como bloque de referencia para interpretar la pregunta 3 (tipo de estudio).
