import { useState } from "react";
import {
  BarChart2, Plus, Trash2, Clock,
  FolderPlus, ChevronRight, AlertTriangle,
} from "lucide-react";

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("es-CO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function SkeletonCard() {
  return (
    <div className="project-card skeleton-card">
      <div className="skeleton skeleton-icon" />
      <div className="skeleton skeleton-title" />
      <div className="skeleton skeleton-meta" />
      <div className="skeleton skeleton-tag" />
    </div>
  );
}

function DeleteConfirmModal({ projectName, onConfirm, onCancel }) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal modal-sm" onClick={(e) => e.stopPropagation()}>
        <div className="modal-warn-icon">
          <AlertTriangle size={22} strokeWidth={2} />
        </div>
        <h2 className="modal-title" style={{ justifyContent: "center", textAlign: "center" }}>
          ¿Eliminar proyecto?
        </h2>
        <p className="modal-warn-text">
          Vas a eliminar <strong>"{projectName}"</strong> y todos sus análisis. Esta acción no se puede deshacer.
        </p>
        <div className="modal-actions" style={{ justifyContent: "center" }}>
          <button className="btn-ghost" onClick={onCancel}>
            Cancelar
          </button>
          <button className="btn-danger" onClick={onConfirm}>
            <Trash2 size={14} strokeWidth={2.5} />
            Sí, eliminar
          </button>
        </div>
      </div>
    </div>
  );
}

export function HomeView({
  projects,
  loadingProjects,
  onOpenProject,
  onCreateProject,
  onDeleteProject,
}) {
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [deleteTarget, setDeleteTarget] = useState(null); // { id, name }

  const handleCreate = () => {
    if (!name.trim()) return;
    onCreateProject({ name: name.trim(), code: code.trim() });
    setName("");
    setCode("");
    setShowModal(false);
  };

  const confirmDelete = (e, project) => {
    e.stopPropagation();
    setDeleteTarget({ id: project.id, name: project.name });
  };

  const handleDeleteConfirmed = () => {
    onDeleteProject(deleteTarget.id);
    setDeleteTarget(null);
  };

  return (
    <div className="home">
      <div className="home-header">
        <div>
          <h1 className="home-title">Proyectos de análisis</h1>
          <p className="home-subtitle">
            Selecciona un proyecto existente o crea uno nuevo para comenzar.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={15} strokeWidth={2.5} />
          Nuevo proyecto
        </button>
      </div>

      <div className="projects-grid">
        {/* Botón crear — siempre primero */}
        <button className="project-card-new" onClick={() => setShowModal(true)}>
          <div className="project-card-new-icon">
            <FolderPlus size={20} strokeWidth={1.8} />
          </div>
          Nuevo proyecto
        </button>

        {/* Skeletons mientras carga */}
        {loadingProjects && [0, 1, 2].map((i) => <SkeletonCard key={i} />)}

        {/* Tarjetas de proyecto */}
        {!loadingProjects &&
          projects.map((p, i) => (
            <div
              key={p.id}
              className="project-card"
              style={{ animationDelay: `${i * 0.05}s` }}
              onClick={() => onOpenProject(p)}
            >
              <div className="project-card-top">
                <div className="project-card-icon">
                  <BarChart2 size={18} strokeWidth={2} />
                </div>
                <div className="project-card-menu" onClick={(e) => e.stopPropagation()}>
                  <button
                    className="btn-icon btn-icon-danger"
                    title="Eliminar proyecto"
                    onClick={(e) => confirmDelete(e, p)}
                  >
                    <Trash2 size={13} strokeWidth={2} />
                  </button>
                </div>
              </div>

              <p className="project-card-name">{p.name}</p>
              {p.code && <p className="project-card-code">{p.code}</p>}
              <p className="project-card-meta">
                <Clock size={11} strokeWidth={2} />
                Actualizado {formatDate(p.updatedAt)}
              </p>

              <div style={{ marginTop: "auto", display: "flex", justifyContent: "flex-end" }}>
                <span className="project-card-open-hint">
                  Abrir <ChevronRight size={13} strokeWidth={2.5} />
                </span>
              </div>
            </div>
          ))}
      </div>

      {/* Modal nuevo proyecto */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">
              <div className="modal-title-icon">
                <FolderPlus size={16} strokeWidth={2} />
              </div>
              Nuevo proyecto
            </h2>
            <div className="modal-field">
              <label>Nombre del proyecto *</label>
              <input
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ej: Estudio salud de marca Q2 2026"
                autoFocus
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              />
            </div>
            <div className="modal-field">
              <label>Código de proyecto</label>
              <input
                className="input"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Ej: BS-2026-042"
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-ghost" onClick={() => setShowModal(false)}>
                Cancelar
              </button>
              <button
                className="btn-primary"
                onClick={handleCreate}
                disabled={!name.trim()}
              >
                <Plus size={14} strokeWidth={2.5} />
                Crear proyecto
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal confirmación eliminar */}
      {deleteTarget && (
        <DeleteConfirmModal
          projectName={deleteTarget.name}
          onConfirm={handleDeleteConfirmed}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
