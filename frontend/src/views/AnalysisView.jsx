import { useState, useEffect, useRef } from "react";
import { ClipboardList, Images, History, Zap, RotateCcw } from "lucide-react";
import { QUESTIONS } from "../constants/questions";
import { ContextWizard } from "../components/ContextWizard";
import { ImagesPanel } from "../components/ImagesPanel";
import { ResultPanel } from "../components/ResultPanel";
import { api } from "../services/api";

const ANALYSIS_STEPS = [
  { key: "uploading",  label: "Subiendo archivos…",   pct: 20 },
  { key: "processing", label: "Procesando imágenes…", pct: 50 },
  { key: "generating", label: "Generando análisis…",  pct: 80 },
  { key: "done",       label: "Finalizando…",         pct: 98 },
];

const EMPTY_ANSWERS = () => {
  const init = {};
  for (const q of QUESTIONS) init[q.id] = "";
  return init;
};

export function AnalysisView({ project }) {
  const [answers, setAnswers] = useState(EMPTY_ANSWERS);
  const [hasPreviousStudy, setHasPreviousStudy] = useState(null);
  const [studyPdf, setStudyPdf] = useState(null);
  const [contextImages, setContextImages] = useState([]);
  const [slideFiles, setSlideFiles] = useState([]);

  // Historial de análisis del proyecto
  const [analyses, setAnalyses] = useState([]);
  const [loadingAnalyses, setLoadingAnalyses] = useState(true);

  const [loading, setLoading] = useState(false);
  const [analysisStep, setAnalysisStep] = useState(null);
  const [analysisPct, setAnalysisPct] = useState(0);
  const [error, setError] = useState("");

  const stepTimerRef = useRef(null);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  // ── Cargar historial al entrar al proyecto ────────────────────────────────
  useEffect(() => {
    setLoadingAnalyses(true);
    api.getAnalyses(project.id)
      .then((data) => {
        setAnalyses(data);
        // Pre-poblar respuestas del análisis más reciente
        if (data.length > 0) {
          const latest = data[0];
          const loadedAnswers = { ...EMPTY_ANSWERS(), ...(latest.answers || {}) };
          setAnswers(loadedAnswers);
          // Restaurar toggle Q10
          const q10 = latest.answers?.q10 || "";
          if (q10.startsWith("Sí")) setHasPreviousStudy("yes");
          else if (q10.startsWith("No")) setHasPreviousStudy("no");
        }
      })
      .catch(() => {})
      .finally(() => setLoadingAnalyses(false));
  }, [project.id]);

  // ── Validación ────────────────────────────────────────────────────────────
  const q10Answered = hasPreviousStudy !== null;
  const allAnswersFilled =
    QUESTIONS.filter((q) => q.id !== "q10").every(
      (q) => answers[q.id]?.trim().length > 0
    ) && q10Answered;

  const canSubmit = allAnswersFilled && slideFiles.length > 0 && !loading;

  // ── Progreso simulado ─────────────────────────────────────────────────────
  const startProgress = () => {
    let stepIdx = 0;
    setAnalysisStep(0);
    setAnalysisPct(ANALYSIS_STEPS[0].pct);
    stepTimerRef.current = setInterval(() => {
      stepIdx += 1;
      if (stepIdx < ANALYSIS_STEPS.length) {
        setAnalysisStep(stepIdx);
        setAnalysisPct(ANALYSIS_STEPS[stepIdx].pct);
      } else {
        clearInterval(stepTimerRef.current);
      }
    }, 3500);
  };

  const stopProgress = (success) => {
    clearInterval(stepTimerRef.current);
    if (success) setAnalysisPct(100);
    setTimeout(() => {
      setAnalysisPct(0);
      setAnalysisStep(null);
    }, 800);
  };

  // ── Submit ────────────────────────────────────────────────────────────────
  const onSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;

    setError("");
    setLoading(true);
    startProgress();

    const fullAnswers = {
      ...answers,
      q10:
        hasPreviousStudy === "yes"
          ? "Sí, se adjunta el estudio cualitativo en PDF."
          : "No existe estudio cualitativo previo.",
    };

    try {
      const fd = new FormData();
      fd.append("project_id", project.id);
      fd.append("contexto_json", JSON.stringify(fullAnswers));
      for (const f of contextImages) fd.append("context_images", f);
      for (const f of slideFiles) fd.append("images", f);
      if (hasPreviousStudy === "yes" && studyPdf) fd.append("study_pdf", studyPdf);

      const res = await fetch(`${API_BASE_URL}/analyze`, { method: "POST", body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || "Error desconocido del servidor.");

      stopProgress(true);

      // Agregar nuevo análisis al inicio del historial
      const newAnalysis = {
        id: data.analysis_id,
        projectId: project.id,
        answers: fullAnswers,
        hasPreviousStudy: fullAnswers.q10,
        slideCount: slideFiles.length,
        contextImageCount: contextImages.length,
        hasPdf: hasPreviousStudy === "yes" && !!studyPdf,
        outputText: data.output_text || "",
        createdAt: new Date().toISOString(),
      };
      setAnalyses((prev) => [newAnalysis, ...prev]);
    } catch (err) {
      stopProgress(false);
      setError(err?.message || "Error inesperado.");
    } finally {
      setLoading(false);
    }
  };

  // ── Reset formulario (no borra el historial) ──────────────────────────────
  const resetAll = () => {
    setAnswers(EMPTY_ANSWERS());
    setHasPreviousStudy(null);
    setStudyPdf(null);
    setContextImages([]);
    setSlideFiles([]);
    setError("");
    clearInterval(stepTimerRef.current);
    setAnalysisStep(null);
    setAnalysisPct(0);
  };

  const currentStepLabel =
    analysisStep !== null ? ANALYSIS_STEPS[analysisStep]?.label : null;

  return (
    <form className="analysis-layout" onSubmit={onSubmit} noValidate>
      {/* ── Panel izquierdo: Contexto ── */}
      <div className="panel context-panel">
        <div className="panel-header">
          <h2 className="panel-title">
            <span className="panel-title-icon">
              <ClipboardList size={13} strokeWidth={2.5} />
            </span>
            Contexto
          </h2>
          <button type="button" className="btn-icon" title="Limpiar formulario" onClick={resetAll}>
            <RotateCcw size={13} strokeWidth={2} />
          </button>
        </div>
        <ContextWizard
          questions={QUESTIONS}
          answers={answers}
          setAnswers={setAnswers}
          hasPreviousStudy={hasPreviousStudy}
          setHasPreviousStudy={setHasPreviousStudy}
          onReset={resetAll}
        />
      </div>

      {/* ── Panel central: Imágenes ── */}
      <div className="panel images-panel">
        <div className="panel-header">
          <h2 className="panel-title">
            <span className="panel-title-icon">
              <Images size={13} strokeWidth={2.5} />
            </span>
            Imágenes
          </h2>
          <button type="submit" className="btn-primary" disabled={!canSubmit}>
            {loading
              ? <><span className="spinner" /> Analizando…</>
              : <><Zap size={14} strokeWidth={2.5} /> Analizar</>
            }
          </button>
        </div>

        {loading && (
          <div className="analysis-progress-bar">
            <div className="analysis-progress-fill" style={{ width: `${analysisPct}%` }} />
            <div className="analysis-progress-steps">
              {ANALYSIS_STEPS.map((s, i) => (
                <span
                  key={s.key}
                  className={`analysis-step${analysisStep !== null && i <= analysisStep ? " active" : ""}${analysisStep !== null && i < analysisStep ? " done" : ""}`}
                >
                  {s.label}
                </span>
              ))}
            </div>
          </div>
        )}

        <ImagesPanel
          contextImages={contextImages}
          setContextImages={setContextImages}
          slideFiles={slideFiles}
          setSlideFiles={setSlideFiles}
          hasPreviousStudy={hasPreviousStudy}
          studyPdf={studyPdf}
          setStudyPdf={setStudyPdf}
        />
      </div>

      {/* ── Panel derecho: Historial ── */}
      <div className="panel output-panel">
        <div className="panel-header">
          <h2 className="panel-title">
            <span className="panel-title-icon">
              <History size={13} strokeWidth={2.5} />
            </span>
            Historial
          </h2>
          {!loadingAnalyses && analyses.length > 0 && (
            <span className="panel-count-badge">{analyses.length} análisis</span>
          )}
        </div>
        <ResultPanel
          analyses={analyses}
          loadingAnalyses={loadingAnalyses}
          loading={loading}
          error={error}
          stepLabel={currentStepLabel}
          analysisPct={analysisPct}
          projectName={project?.name ?? "Análisis"}
          projectCode={project?.code ?? ""}
        />
      </div>
    </form>
  );
}
