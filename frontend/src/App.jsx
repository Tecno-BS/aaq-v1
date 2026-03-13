import { useState, useEffect } from "react";
import "./App.css";
import { HomeView } from "./views/HomeView";
import { AnalysisView } from "./views/AnalysisView";
import { ChevronLeft } from "lucide-react";
import { api } from "./services/api";

export default function App() {
  const [projects, setProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [loadingProjects, setLoadingProjects] = useState(true);

  // Cargar proyectos desde el backend al montar
  useEffect(() => {
    setLoadingProjects(true);
    api.getProjects()
      .then(setProjects)
      .catch(() => {})
      .finally(() => setLoadingProjects(false));
  }, []);

  const handleCreateProject = async (data) => {
    const project = await api.createProject(data);
    setProjects((prev) => [project, ...prev]);
    setActiveProject(project);
  };

  const handleDeleteProject = async (id) => {
    await api.deleteProject(id);
    setProjects((prev) => prev.filter((p) => p.id !== id));
    if (activeProject?.id === id) setActiveProject(null);
  };

  const handleOpenProject = async (project) => {
    setActiveProject(project);
    await api.updateProject(project.id, {}).catch(() => {});
    setProjects((prev) =>
      prev.map((p) =>
        p.id === project.id ? { ...p, updatedAt: new Date().toISOString() } : p
      )
    );
  };

  const handleGoHome = () => setActiveProject(null);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-brand" onClick={handleGoHome}>
          <div className="topbar-logo">
            <img src="/bs-logo-180x180.png" alt="Brandstrat" />
          </div>
          <span className="topbar-name">
            brandstrat <span>/ AAQ Análisis cuantitativo</span>
          </span>
        </div>

        <div className="topbar-right">
          {activeProject && (
            <span className="topbar-project" title={activeProject.name}>
              {activeProject.code ? `[${activeProject.code}] ` : ""}
              {activeProject.name}
            </span>
          )}
          {activeProject && (
            <button className="btn-ghost" onClick={handleGoHome}>
              <ChevronLeft size={14} strokeWidth={2.5} />
              Proyectos
            </button>
          )}
        </div>
      </header>

      {activeProject ? (
        <AnalysisView project={activeProject} />
      ) : (
        <HomeView
          projects={projects}
          loadingProjects={loadingProjects}
          onOpenProject={handleOpenProject}
          onCreateProject={handleCreateProject}
          onDeleteProject={handleDeleteProject}
        />
      )}
    </div>
  );
}
