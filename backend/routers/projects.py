from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.project import Project
from models.analysis import Analysis

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name : str
    code : Optional[str] = None

class ProjectUpdate(BaseModel):
    name : Optional[str] = None
    code : Optional[str] = None

def _fmt(p: Project) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "code": p.code,
        "createdAt": p.created_at.isoformat(),
        "updatedAt": p.updated_at.isoformat(),
    }


@router.get("/", response_model=List[dict])
async def list_projects():
    projects = await Project.find_all().sort(-Project.updated_at).to_list()
    return [_fmt(p) for p in projects]


@router.post("/", response_model=dict, status_code=201)
async def create_project(body: ProjectCreate):
    project = Project(name=body.name, code=body.code)
    await project.insert()
    return _fmt(project)

@router.put("/{project_id}", response_model=dict)
async def update_project(project_id: str, body: ProjectUpdate):
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if body.name is not None:
        project.name = body.name
    if body.code is not None:
        project.code = body.code
    project.updated_at = datetime.now(timezone.utc)
    await project.save()
    return _fmt(project)

@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str):
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    #Eliminar también analisis asociados al proyecto 
    await Analysis.find(Analysis.project_id == project_id).delete()
    await project.delete()

@router.get("/{project_id}/analyses", response_model=List[dict])
async def list_analyses(project_id: str):
    analyses = (
        await Analysis.find(Analysis.project_id == project_id)
        .sort(-Analysis.created_at)
        .to_list()
    )

    return [
        {
            "id": str(a.id),
            "projectId": a.project_id,
            "answers": a.answers,
            "hasPreviousStudy": a.has_previous_study,
            "slideCount": len(a.slide_paths),
            "contextImageCount": len(a.context_image_paths),
            "hasPdf": a.pdf_path is not None,
            "outputText": a.output_text,
            "createdAt": a.created_at.isoformat(),   
        }
        for a in analyses
    ]