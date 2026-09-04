"""API 路由模块 / API router module."""

from .ingest import router as ingest_router
from .chat import router as chat_router
from .sessions import router as sessions_router
from .scenes import router as scenes_router
from .health import router as health_router

__all__ = [
    "ingest_router",
    "chat_router",
    "sessions_router",
    "scenes_router",
    "health_router",
]