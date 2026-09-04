"""会话管理 API / Session management API."""

from fastapi import APIRouter, HTTPException

from app.core.rag import RAGManager
from app.core.sessions import session_store
from app.schemas.session import SessionCreate, SessionInfo, SessionList

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=SessionList)
async def list_sessions() -> dict:
    """列出当前所有会话（含消息数/创建时间）。"""
    sessions = session_store.list()
    # 按创建时间倒序 / Sort by created time descending
    sessions.sort(key=lambda s: s["created_at"], reverse=True)
    return {"sessions": sessions}


@router.post("", response_model=SessionInfo)
async def create_session(body: SessionCreate) -> dict:
    """创建一个新会话。</strong>"""
    manager = RAGManager()
    manager.create_session(body.id)
    return session_store.create(body.id)


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict:
    """删除一个会话（含框架记忆）。"""
    manager = RAGManager()
    manager.clear_session(session_id)
    session_store.delete(session_id)
    return {"ok": True, "id": session_id}