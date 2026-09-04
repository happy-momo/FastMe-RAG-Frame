"""场景 API / Scene API."""

from fastapi import APIRouter

from app.core.rag import RAGManager
from app.schemas.health import SceneInfo

router = APIRouter(prefix="/api/scenes", tags=["scenes"])


@router.get("", response_model=list[SceneInfo])
async def list_scenes() -> list:
    """列出所有可用的问答场景。"""
    return RAGManager().get_scenes()