"""健康检查 API / Health check API."""

from pathlib import Path

from fastapi import APIRouter

from app.core.rag import RAGManager
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> dict:
    """探活：LLM 连通性 + 向量库数量 + 模型目录。"""
    manager = RAGManager()
    return {
        "status": "ok",
        "llm_reachable": manager.llm_reachable(),
        "vector_count": manager.get_vector_count(),
        "models_dir": str(Path("models").resolve()),
    }