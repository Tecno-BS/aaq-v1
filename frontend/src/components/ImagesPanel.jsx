import { useMemo, useState, useEffect } from "react";
import { Upload, Images, Paperclip, X, FileText, ZoomIn } from "lucide-react";

/* ─── Lightbox ────────────────────────────────────────────────────────────── */
function Lightbox({ src, name, onClose }) {
  // Cerrar con Escape
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="lightbox-overlay" onClick={onClose}>
      <div className="lightbox-inner" onClick={(e) => e.stopPropagation()}>
        <div className="lightbox-header">
          <span className="lightbox-name">{name}</span>
          <button className="lightbox-close" onClick={onClose} title="Cerrar (Esc)">
            <X size={16} strokeWidth={2.5} />
          </button>
        </div>
        <img src={src} alt={name} className="lightbox-img" />
      </div>
    </div>
  );
}

/* ─── Miniaturas ──────────────────────────────────────────────────────────── */
function FileThumbs({ files, onRemove, onPreview }) {
  if (!files.length) return null;
  return (
    <div className="thumb-grid">
      {files.map((f, i) => {
        const url = URL.createObjectURL(f);
        return (
          <div key={`${f.name}-${i}`} className="thumb-item">
            <div
              className="thumb-img-wrap"
              onClick={() => onPreview(url, f.name)}
              title="Ver a tamaño completo"
            >
              <img src={url} alt={f.name} />
              <div className="thumb-zoom-hint">
                <ZoomIn size={14} strokeWidth={2} />
              </div>
            </div>
            <div className="thumb-label">{f.name}</div>
            {onRemove && (
              <button type="button" className="thumb-remove" onClick={() => onRemove(i)}>
                <X size={10} strokeWidth={3} />
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ─── Drop Zone ───────────────────────────────────────────────────────────── */
function DropZone({ label, meta, onChange, accept, icon: Icon = Upload }) {
  return (
    <label className="file-drop">
      <input
        type="file"
        className="file-input"
        accept={accept || "image/png,image/jpeg,image/webp"}
        multiple={accept === undefined}
        onChange={onChange}
      />
      <div className="file-drop-inner">
        <div className="file-drop-icon">
          <Icon size={17} strokeWidth={1.8} />
        </div>
        <div>
          <div className="file-drop-text">{label}</div>
          <div className="file-drop-meta">{meta}</div>
        </div>
      </div>
    </label>
  );
}

/* ─── Panel principal ─────────────────────────────────────────────────────── */
export function ImagesPanel({
  contextImages, setContextImages,
  slideFiles, setSlideFiles,
  hasPreviousStudy, studyPdf, setStudyPdf,
}) {
  const [preview, setPreview] = useState(null); // { src, name } | null

  const slideInfo = useMemo(() => {
    const totalMB = (slideFiles.reduce((a, f) => a + (f?.size || 0), 0) / (1024 * 1024)).toFixed(2);
    return `${slideFiles.length} slide(s) · ${totalMB} MB`;
  }, [slideFiles]);

  const ctxInfo = useMemo(() => {
    const totalMB = (contextImages.reduce((a, f) => a + (f?.size || 0), 0) / (1024 * 1024)).toFixed(2);
    return `${contextImages.length} imagen(es) · ${totalMB} MB`;
  }, [contextImages]);

  // Capturar los archivos en un array local ANTES de resetear el input,
  // porque en React 18 el updater corre tras el event handler (cuando
  // e.target.value = "" ya limpió el FileList).
  const addSlideFiles = (e) => {
    const picked = Array.from(e.target.files || []);
    e.target.value = "";
    if (picked.length > 0) setSlideFiles((p) => [...p, ...picked]);
  };
  const removeSlide = (idx) => setSlideFiles((p) => p.filter((_, i) => i !== idx));

  const addContext = (e) => {
    const picked = Array.from(e.target.files || []);
    e.target.value = "";
    if (picked.length > 0) setContextImages((p) => [...p, ...picked]);
  };
  const removeContext = (idx) => setContextImages((p) => p.filter((_, i) => i !== idx));

  const onPickPdf = (e) => {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (f) setStudyPdf(f);
  };

  const openPreview = (src, name) => setPreview({ src, name });
  const closePreview = () => setPreview(null);

  return (
    <>
      <div className="panel-body">
        {/* Slides */}
        <p className="images-section-label">
          <Images size={13} strokeWidth={2} />
          Slides del reporte
          <span className="required">*</span>
        </p>
        <DropZone
          label="Arrastra o haz clic para agregar slides"
          meta={slideFiles.length > 0 ? slideInfo : "PNG, JPG o WebP · máx. 7 MB por imagen"}
          onChange={addSlideFiles}
          icon={Upload}
        />
        {slideFiles.length > 0 && (
          <div className="thumb-count-badge">
            <Images size={12} strokeWidth={2} />
            {slideFiles.length} slide(s) cargado(s)
          </div>
        )}
        <FileThumbs files={slideFiles} onRemove={removeSlide} onPreview={openPreview} />

        <div className="divider" />

        {/* Material de contexto */}
        <p className="images-section-label">
          <Paperclip size={13} strokeWidth={2} />
          Material de contexto
          <span style={{ fontSize: 10, color: "var(--bs-muted2)", fontWeight: 500, marginLeft: 2 }}>(opcional)</span>
        </p>
        <DropZone
          label="Briefing, funnel, esquemas…"
          meta={contextImages.length > 0 ? ctxInfo : "Imágenes adicionales de referencia"}
          onChange={addContext}
          icon={Paperclip}
        />
        {contextImages.length > 0 && (
          <div className="thumb-count-badge">
            <Paperclip size={12} strokeWidth={2} />
            {contextImages.length} imagen(es) de contexto
          </div>
        )}
        <FileThumbs files={contextImages} onRemove={removeContext} onPreview={openPreview} />

        {/* PDF estudio cualitativo */}
        {hasPreviousStudy === "yes" && (
          <>
            <div className="divider" />
            <p className="images-section-label">
              <FileText size={13} strokeWidth={2} />
              Estudio cualitativo previo (PDF)
            </p>
            {studyPdf ? (
              <div className="pdf-file-item">
                <div className="pdf-file-icon">
                  <FileText size={18} strokeWidth={1.8} />
                </div>
                <div className="pdf-file-info">
                  <span className="pdf-file-name">{studyPdf.name}</span>
                  <span className="pdf-file-size">
                    {(studyPdf.size / (1024 * 1024)).toFixed(2)} MB
                  </span>
                </div>
                <button
                  type="button"
                  className="btn-icon"
                  onClick={() => setStudyPdf(null)}
                  title="Quitar PDF"
                >
                  <X size={13} strokeWidth={2.5} />
                </button>
              </div>
            ) : (
              <DropZone
                label="Sube el informe cualitativo en PDF"
                meta="Solo un archivo · máx. 20 MB"
                onChange={onPickPdf}
                accept="application/pdf"
                icon={FileText}
              />
            )}
          </>
        )}
      </div>

      {/* Lightbox */}
      {preview && (
        <Lightbox src={preview.src} name={preview.name} onClose={closePreview} />
      )}
    </>
  );
}
