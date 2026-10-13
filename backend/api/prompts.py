from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import prompts as svc

class ProjectIn(BaseModel):
    name: str = Field(min_length=2)
    description: str = ""

class VersionIn(BaseModel):
    template: str = Field(min_length=4)
    notes: str = ""
    variables: dict[str, str] | None = None

class PreviewIn(BaseModel):
    variables: dict[str, str] | None = None

router = APIRouter()

@router.get("/projects")
async def projects(db: AsyncSession = Depends(get_db)):
    rows = await svc.list_projects(db)
    return {"projects": [{"id": p.id, "name": p.name, "description": p.description} for p in rows]}

@router.post("/projects")
async def create_project(payload: ProjectIn, db: AsyncSession = Depends(get_db)):
    row = await svc.create_project(db, payload.name, payload.description)
    return {"id": row.id, "name": row.name}

@router.get("/projects/{project_id}/versions")
async def versions(project_id: str, db: AsyncSession = Depends(get_db)):
    rows = await svc.list_versions(db, project_id)
    return {
        "versions": [
            {"id": v.id, "version": v.version, "template": v.template[:200], "notes": v.notes}
            for v in rows
        ]
    }

@router.post("/projects/{project_id}/versions")
async def add_version(project_id: str, payload: VersionIn, db: AsyncSession = Depends(get_db)):
    try:
        row = await svc.add_version(db, project_id, payload.template, payload.notes, payload.variables)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"id": row.id, "version": row.version}

@router.post("/versions/{version_id}/preview")
async def preview(version_id: str, payload: PreviewIn, db: AsyncSession = Depends(get_db)):
    try:
        return await svc.preview(db, version_id, payload.variables)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
