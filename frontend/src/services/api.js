const BASE = import.meta.env.VITE_API_BASE_URL;

async function handleResponse(response){
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Error desconocido del servidor.");
    }
    if (response.status === 204) return null;
    return response.json()
}

export const api = {
    getProjects: () => 
        fetch(`${BASE}/projects`).then(handleResponse),

    createProject : (body) =>
        fetch(`${BASE}/projects`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
    }).then(handleResponse),
    
    updateProject : (id, body) =>
        fetch(`${BASE}/projects/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        }).then(handleResponse),
    
    deleteProject : (id) =>
        fetch(`${BASE}/projects/${id}`, { method: "DELETE" }).then(handleResponse),

    getAnalyses : (projectId) =>
        fetch(`${BASE}/projects/${projectId}/analyses`).then(handleResponse),
};