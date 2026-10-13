from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import prompts as svc

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, project_id: str | None = None, version_id: str | None = None, db: AsyncSession = Depends(get_db)):
    projects = await svc.list_projects(db)
    versions = await svc.list_versions(db, project_id) if project_id else []
    if not version_id and versions:
        version_id = versions[0].id
    previews = await svc.list_previews(db, version_id) if version_id else []
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Prompt Studio Workspace",
            "projects": projects,
            "project_id": project_id,
            "versions": versions,
            "version_id": version_id,
            "previews": previews,
        },
    )

@router.post("/ui/projects")
async def ui_proj(name: str = Form(...), db: AsyncSession = Depends(get_db)):
    row = await svc.create_project(db, name)
    return RedirectResponse(f"/?project_id={row.id}", status_code=303)

@router.post("/ui/versions")
async def ui_ver(project_id: str = Form(...), template: str = Form(...), db: AsyncSession = Depends(get_db)):
    row = await svc.add_version(db, project_id, template)
    return RedirectResponse(f"/?project_id={project_id}&version_id={row.id}", status_code=303)

@router.post("/ui/preview")
async def ui_preview(version_id: str = Form(...), db: AsyncSession = Depends(get_db)):
    from backend.models import PromptVersion

    await svc.preview(db, version_id, {})
    ver = await db.get(PromptVersion, version_id)
    pid = ver.project_id if ver else ""
    return RedirectResponse(f"/?project_id={pid}&version_id={version_id}", status_code=303)
