import {
  Sparkles, ClipboardList, FileDown, Loader2,
  Calendar, Images, Paperclip, FileText, History,
} from "lucide-react";
import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("es-CO", {
    day: "2-digit", month: "short", year: "numeric",
  }) + "  ·  " + d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
}

// ─── Tarjeta de análisis individual ──────────────────────────────────────────
function AnalysisCard({ analysis, version, total, projectName, projectCode }) {
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    if (downloading || !analysis.outputText) return;
    setDownloading(true);
    try {
      const res = await fetch(`${API_BASE}/export-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          output_text: analysis.outputText,
          project_name: projectName,
          project_code: projectCode,
        }),
      });
      if (!res.ok) throw new Error("Error al generar PDF");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const disposition = res.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename="?([^"]+)"?/);
      a.download = match?.[1] ?? `analisis_v${version}_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    } finally {
      setDownloading(false);
    }
  };

  const isLatest = version === total;

  return (
    <div className={`acard${isLatest ? " acard-latest" : ""}`}>
      <div className="acard-header">
        <div className="acard-version-wrap">
          <span className="acard-version">v{version}</span>
          {isLatest && <span className="acard-latest-badge">Último</span>}
        </div>
        <button
          className="btn-pdf acard-download"
          onClick={handleDownload}
          disabled={downloading || !analysis.outputText}
          title="Descargar este análisis como PDF"
        >
          {downloading
            ? <><Loader2 size={13} strokeWidth={2} className="spin-anim" /> PDF…</>
            : <><FileDown size={13} strokeWidth={2} /> PDF</>
          }
        </button>
      </div>

      <div className="acard-date">
        <Calendar size={11} strokeWidth={2} />
        {formatDate(analysis.createdAt)}
      </div>

      <div className="acard-meta">
        {analysis.slideCount > 0 && (
          <span className="acard-chip">
            <Images size={10} strokeWidth={2} />
            {analysis.slideCount} slide{analysis.slideCount !== 1 ? "s" : ""}
          </span>
        )}
        {analysis.contextImageCount > 0 && (
          <span className="acard-chip">
            <Paperclip size={10} strokeWidth={2} />
            {analysis.contextImageCount} contexto
          </span>
        )}
        {analysis.hasPdf && (
          <span className="acard-chip">
            <FileText size={10} strokeWidth={2} />
            PDF cualitativo
          </span>
        )}
      </div>
    </div>
  );
}

// ─── Skeleton de carga ────────────────────────────────────────────────────────
function HistorySkeleton() {
  return (
    <div className="acard-skeleton-list">
      {[0, 1, 2].map((i) => (
        <div key={i} className="acard acard-skeleton">
          <div className="skeleton skeleton-version" />
          <div className="skeleton skeleton-date" />
          <div className="skeleton skeleton-chips" />
        </div>
      ))}
    </div>
  );
}

// ─── Panel principal ──────────────────────────────────────────────────────────
export function ResultPanel({
  analyses,
  loadingAnalyses,
  loading,
  error,
  stepLabel,
  analysisPct,
  projectName = "Análisis",
  projectCode = "",
}) {
  const total = analyses.length;

  return (
    <div className="panel-body">
      {/* ── Procesando nuevo análisis ── */}
      {loading && (
        <div className="loading-state">
          <div className="loading-icon loading-icon-pulse">
            <Sparkles size={22} strokeWidth={1.8} />
          </div>
          <p className="loading-text">{stepLabel ?? "Analizando slides…"}</p>
          <p className="loading-subtext">
            El modelo está procesando el contexto e imágenes.
            <br />Esto puede tomar unos segundos.
          </p>
          <div className="result-progress-wrap">
            <div
              className="result-progress-fill"
              style={{ width: `${analysisPct ?? 0}%` }}
            />
          </div>
          <span className="result-progress-pct">{analysisPct ?? 0}%</span>
        </div>
      )}

      {/* ── Error ── */}
      {!loading && error && (
        <div className="alert" style={{ marginBottom: 12 }}>{error}</div>
      )}

      {/* ── Cargando historial ── */}
      {!loading && loadingAnalyses && <HistorySkeleton />}

      {/* ── Sin análisis ── */}
      {!loading && !loadingAnalyses && total === 0 && (
        <div className="output-empty">
          <div className="output-empty-icon">
            <History size={22} strokeWidth={1.5} />
          </div>
          <p className="output-empty-title">Sin análisis aún</p>
          <p className="output-empty-text">
            Completa el contexto, sube tus slides y presiona <strong>Analizar</strong>.
          </p>
          <div className="output-steps">
            {[
              "Responde las 10 preguntas de contexto",
              "Sube las imágenes de tus slides",
              "Presiona Analizar",
            ].map((s, i) => (
              <div className="output-step" key={i}>
                <div className="output-step-num">{i + 1}</div>
                {s}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Historial ── */}
      {!loading && !loadingAnalyses && total > 0 && (
        <div className="acard-list">
          {analyses.map((a, i) => (
            <AnalysisCard
              key={a.id}
              analysis={a}
              version={total - i}
              total={total}
              projectName={projectName}
              projectCode={projectCode}
            />
          ))}
        </div>
      )}
    </div>
  );
}
