from __future__ import annotations
import json
import re
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.llm import get_llm
from backend.models import PreviewRun, PromptProject, PromptVersion
from backend.utils.ids import short_id

_VAR = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

def render_template(template: str, variables: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return _VAR.sub(repl, template)

def extract_variables(template: str) -> list[str]:
    return sorted(set(_VAR.findall(template)))

async def create_project(session: AsyncSession, name: str, description: str = "") -> PromptProject:
    proj = PromptProject(id=short_id(), name=name.strip()[:160], description=description.strip())
    session.add(proj)
    await session.commit()
    await session.refresh(proj)
    return proj

async def list_projects(session: AsyncSession) -> list[PromptProject]:
    return list((await session.execute(select(PromptProject).order_by(PromptProject.name))).scalars())

async def add_version(
    session: AsyncSession, project_id: str, template: str, notes: str = "", variables: dict | None = None
) -> PromptVersion:
    proj = await session.get(PromptProject, project_id)
    if not proj:
        raise ValueError("project not found")
    max_v = (
        await session.execute(
            select(func.max(PromptVersion.version)).where(PromptVersion.project_id == project_id)
        )
    ).scalar()
    next_v = int(max_v or 0) + 1
    vars_json = json.dumps(variables or {k: "" for k in extract_variables(template)})
    ver = PromptVersion(
        id=short_id(),
        project_id=project_id,
        version=next_v,
        template=template.strip(),
        variables_json=vars_json,
        notes=notes.strip(),
    )
    session.add(ver)
    await session.commit()
    await session.refresh(ver)
    return ver

async def list_versions(session: AsyncSession, project_id: str) -> list[PromptVersion]:
    stmt = select(PromptVersion).where(PromptVersion.project_id == project_id).order_by(PromptVersion.version.desc())
    return list((await session.execute(stmt)).scalars())

async def preview(
    session: AsyncSession, version_id: str, variables: dict[str, str] | None = None
) -> dict:
    ver = await session.get(PromptVersion, version_id)
    if not ver:
        raise ValueError("version not found")
    base = json.loads(ver.variables_json or "{}")
    merged = {**base, **(variables or {})}
    rendered = render_template(ver.template, {k: str(v) for k, v in merged.items()})
    llm = get_llm()
    output = await llm.complete(rendered, system="Follow the prompt instructions precisely.")
    run = PreviewRun(id=short_id(), version_id=version_id, rendered=rendered, output=output)
    session.add(run)
    await session.commit()
    return {"rendered": rendered, "output": output, "preview_id": run.id}

async def list_previews(session: AsyncSession, version_id: str) -> list[PreviewRun]:
    stmt = select(PreviewRun).where(PreviewRun.version_id == version_id).order_by(PreviewRun.created_at.desc())
    return list((await session.execute(stmt)).scalars())
