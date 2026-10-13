from fastapi import APIRouter
from backend.api import health, prompts, ui
api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(prompts.router, prefix="/api", tags=["prompts"])
api_router.include_router(ui.router, tags=["ui"])
