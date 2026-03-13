import { useState } from "react";
import { CheckCircle2, ChevronDown, ChevronUp, RotateCcw, FileText } from "lucide-react";

function Q10Toggle({ hasPreviousStudy, setHasPreviousStudy }) {
  return (
    <div className="q10-toggle-wrapper">
      <p className="question-description">
        ¿Existe un estudio cualitativo anterior? Si es así, sube el PDF en el panel de imágenes.
      </p>
      <div className="q10-toggle">
        <button
          type="button"
          className={`q10-option${hasPreviousStudy === "yes" ? " active" : ""}`}
          onClick={() => setHasPreviousStudy("yes")}
        >
          <CheckCircle2 size={14} strokeWidth={2.5} />
          Sí, tengo un estudio previo
        </button>
        <button
          type="button"
          className={`q10-option${hasPreviousStudy === "no" ? " active" : ""}`}
          onClick={() => setHasPreviousStudy("no")}
        >
          No aplica
        </button>
      </div>
      {hasPreviousStudy === "yes" && (
        <div className="q10-hint">
          <FileText size={13} strokeWidth={2} />
          Sube el PDF del estudio cualitativo en el panel central.
        </div>
      )}
    </div>
  );
}

export function ContextWizard({
  questions,
  answers,
  setAnswers,
  hasPreviousStudy,
  setHasPreviousStudy,
  onReset,
}) {
  const [openId, setOpenId] = useState(questions[0]?.id ?? null);

  const filledCount =
    questions.filter((q) => {
      if (q.id === "q10") return hasPreviousStudy !== null;
      return !!answers[q.id]?.trim();
    }).length;

  const progress = Math.round((filledCount / questions.length) * 100);

  const toggle = (id) => setOpenId((prev) => (prev === id ? null : id));

  return (
    <>
      <div className="context-progress">
        <div className="progress-bar-track">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
        <div className="progress-meta">
          <span>{filledCount} de {questions.length} respondidas</span>
          <span style={{ fontWeight: 600, color: progress === 100 ? "var(--bs-orange)" : undefined }}>
            {progress}%
          </span>
        </div>
      </div>

      <div className="panel-body">
        {questions.map((q, i) => {
          const isQ10 = q.id === "q10";
          const isFilled = isQ10
            ? hasPreviousStudy !== null
            : !!answers[q.id]?.trim();
          const isOpen = openId === q.id;

          return (
            <div
              key={q.id}
              className={`question-item${isFilled ? " is-filled" : ""}`}
              style={{ animationDelay: `${i * 0.03}s` }}
            >
              <div className="question-item-header" onClick={() => toggle(q.id)}>
                <div className="question-item-left">
                  <div className="question-num">{i}</div>
                  <span className="question-label">{q.title}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  {isFilled && (
                    <span className="question-check">
                      <CheckCircle2 size={14} strokeWidth={2.5} />
                    </span>
                  )}
                  {isOpen
                    ? <ChevronUp size={14} strokeWidth={2} color="var(--bs-muted2)" />
                    : <ChevronDown size={14} strokeWidth={2} color="var(--bs-muted2)" />
                  }
                </div>
              </div>

              {isOpen && (
                <div className="question-item-body">
                  {isQ10 ? (
                    <Q10Toggle
                      hasPreviousStudy={hasPreviousStudy}
                      setHasPreviousStudy={setHasPreviousStudy}
                    />
                  ) : (
                    <>
                      <p className="question-description">{q.description}</p>
                      <textarea
                        className="textarea"
                        rows={5}
                        value={answers[q.id]}
                        onChange={(e) =>
                          setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))
                        }
                        placeholder={q.placeholder}
                        autoFocus
                      />
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {filledCount > 0 && (
          <button
            type="button"
            className="btn-ghost"
            onClick={onReset}
            style={{ width: "100%", marginTop: 8, justifyContent: "center" }}
          >
            <RotateCcw size={13} strokeWidth={2} />
            Limpiar respuestas
          </button>
        )}
      </div>
    </>
  );
}
